#
# Copyright (C) 2016
#      The Board of Trustees of the Leland Stanford Junior University
# Written by Stephane Thiell <sthiell@stanford.edu>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SES utilities

Requires sg_ses from sg3_utils (recent version, like 1.77).
"""

import logging
import re
import subprocess
from retrying import retry
import fasteners

__author__ = 'sthiell@stanford.edu (Stephane Thiell)'

LOGGER = logging.getLogger(__name__)


@retry(stop_max_attempt_number=10, wait_random_min=1000, wait_random_max=10000)
@fasteners.interprocess_locked('/tmp/sg_ses_lock')
def ses_get_snic_nickname(sg_name):
    """Get subenclosure nickname (SES-2) [snic]"""
    # SES nickname is not available through sysfs, use sg_ses tool instead
    cmdargs = ['sg_ses', '--page=snic', '-I0', '/dev/' + sg_name]
    LOGGER.debug('ses_get_snic_nickname: executing: %s', cmdargs)
    try:
        stdout, stderr = subprocess.Popen(cmdargs,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
    except OSError as err:
        LOGGER.warning('ses_get_snic_nickname: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_snic_nickname: sg_ses(stderr): %s', line)

    for line in stdout.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_snic_nickname: sg_ses: %s', line)
        mobj = re.match(r'\s+nickname:\s*([^ ]+)', line)
        if mobj:
            return mobj.group(1)


def ses_get_enclosure_from_wwn(wwn):
    """Return the sg device of the enclosure with the provided wwn"""
    cmdargs = ['lsscsi', '-g']
    LOGGER.debug('ses_get_enclosure_from_wwn: executing: %s', cmdargs)
    try:
        stdout, stderr = subprocess.Popen(cmdargs,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
    except OSError as err:
        LOGGER.warning('ses_get_enclosure_from_wwn: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_enclosure_from_wwn: sg_ses(stderr): %s', line)
        raise subprocess.CalledProcessError

    for line in stdout.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_enclosure_from_wwn: sg_ses: %s', line)
        if 'enclosu' in line:
            mobj = re.match(r'.*\/dev\/(sg\d+)', line)
            sg = mobj.group(1)
            test = ses_get_enclosure_wwn_from_sg(sg)
            if test == wwn:
                return sg
    return None # Enclosure not found

@retry(stop_max_attempt_number=10, wait_random_min=1000, wait_random_max=10000)
@fasteners.interprocess_locked('/tmp/sg_ses_lock')
def ses_get_enclosure_wwn_from_sg(sg_name):
    """Get the WWN of a enclosure from the sg device"""
    cmdargs = ['sg_ses', '--page=0x01', '/dev/' + sg_name]
    LOGGER.debug('ses_get_enclosure_from_wwn: executing: %s', cmdargs)
    try:
        stdout, stderr = subprocess.Popen(cmdargs,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
    except OSError as err:
        LOGGER.warning('ses_get_enclosure_from_wwn: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_enclosure_from_wwn: sg_ses(stderr): %s', line)
        raise subprocess.CalledProcessError

    for line in stdout.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_enclosure_from_wwn: sg_ses: %s', line)
        mobj = re.match(r'^\s+enclosure logical identifier \(hex\): (\w+)$', line)
        if mobj:
            return "0x{}".format(mobj.group(1))

@retry(stop_max_attempt_number=10, wait_random_min=1000, wait_random_max=10000)
@fasteners.interprocess_locked('/tmp/sg_ses_lock')
def ses_get_id_xyratex(sg_name):
    """Get the ID on the LED display on the front of the JBOD"""
    cmdargs = ['sg_ses', '--page=0x02', '--index=14,0', '/dev/' + sg_name]
    LOGGER.debug('ses_get_id_xyratex: executing: %s', cmdargs)
    try:
        stdout, stderr = subprocess.Popen(cmdargs,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
    except OSError as err:
        LOGGER.warning('ses_get_id_xyratex: %s', err)
        return None

    for line in stderr.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_id_xyratex: sg_ses(stderr): %s', line)
        raise subprocess.CalledProcessError

    for line in stdout.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_id_xyratex: sg_ses: %s', line)
        # The last 2 digits contain the ID in hex
        mobj = re.match(r'\s+Vendor specific element type, status in hex: 01 00 00 ([0-9]+)', line)
        if mobj:
            return int(mobj.group(1), 16)


def _ses_get_ed_line(sg_name):
    """Helper function to get element descriptor associated lines."""
    cmdargs = ['sg_ses', '--page=ed', '--join', '/dev/' + sg_name]
    LOGGER.debug('ses_get_ed_metrics: executing: %s', cmdargs)
    stdout, stderr = subprocess.Popen(cmdargs,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()

    for line in stderr.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_ed_metrics: sg_ses(stderr): %s', line)

    element_type = None
    descriptor = None

    for line in stdout.decode("utf-8").splitlines():
        LOGGER.debug('ses_get_ed_metrics: sg_ses: %s', line)
        if line and line[0] != ' ' and 'Element type:' in line:
            # Voltage  3.30V [6,0]  Element type: Voltage sensor
            mobj = re.search(r'([^\[]+)\[.*\][\s,]*Element type:\s*(.+)', line)
            if mobj:
                element_type = mobj.group(2).strip().replace(' ', '_')
                descriptor = mobj.group(1).strip()
                descriptor = descriptor.replace(' ', '_').replace('.', '_')
        else:
            yield element_type, descriptor, line.strip()


def ses_get_ed_metrics(sg_name):
    """
    Return environment metrics as a dictionary from the SES Element
    Descriptor page.
    """
    for element_type, descriptor, line in _ses_get_ed_line(sg_name):
        # Look for environment metrics
        mobj = re.search(r'(\w+)[:=]\s*([-+]*[0-9]+(\.[0-9]+)?)\s+(\w+)', line)
        if mobj:
            key, value, unit = mobj.group(1, 2, 4)
            yield dict((('element_type', element_type),
                        ('descriptor', descriptor), ('key', key),
                        ('value', value), ('unit', unit)))


def ses_get_ed_status(sg_name):
    """
    Return different status code as a dictionary from the SES Element
    Descriptor page.
    """
    for element_type, descriptor, line in _ses_get_ed_line(sg_name):
        # Look for status info
        mobj = re.search(r'status:\s*(.+)', line)
        if mobj:
            status = mobj.group(1).replace(' ', '_')
            yield dict((('element_type', element_type),
                        ('descriptor', descriptor), ('status', status)))
