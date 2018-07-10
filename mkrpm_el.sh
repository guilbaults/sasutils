#!/bin/bash
# Build RPM for RHEL/CentOS
# eg. ./mkrpm_el.sh el7
dist=$1
[ -z "$dist" ] && echo "$0 {dist}" && exit 1
spectool -g -R sasutils-$dist.spec
rpmbuild --define "dist .$dist" -ba sasutils-$dist.spec

# Quick workaround to build the dependencies rpm for python 3.4 

mkdir -p ~/sasutils_extra_rpm/RPMs
cd ~/sasutils_extra_rpm

wget --no-clobber https://files.pythonhosted.org/packages/f4/6f/41b835c9bf69b03615630f8a6f6d45dafbec95eb4e2bb816638f043552b2/fasteners-0.14.1.tar.gz
tar -xvf fasteners-0.14.1.tar.gz
cd fasteners-0.14.1
python3.4 setup.py bdist --formats=rpm
mv dist/fasteners-0.14.1-1.noarch.rpm ../RPMs/python-fasteners-0.14.1-1.noarch.rpm

cd ~/sasutils_extra_rpm
wget --no-clobber https://files.pythonhosted.org/packages/19/c1/27f722aaaaf98786a1b338b78cf60960d9fe4849825b071f4e300da29589/monotonic-1.5.tar.gz
tar -xvf monotonic-1.5.tar.gz
cd monotonic-1.5
python3.4 setup.py bdist --formats=rpm
mv dist/monotonic-1.5-1.noarch.rpm ../RPMs/python-monotonic-1.5-1.noarch.rpm

cd ~/sasutils_extra_rpm
wget --no-clobber https://files.pythonhosted.org/packages/16/d8/bc6316cf98419719bd59c91742194c111b6f2e85abac88e496adefaf7afe/six-1.11.0.tar.gz
tar -xvf six-1.11.0.tar.gz
cd six-1.11.0
python3.4 setup.py bdist --formats=rpm
mv dist/six-1.11.0-1.noarch.rpm ../RPMs/python-six-1.11.0-1.noarch.rpm

cd ~/sasutils_extra_rpm
wget --no-clobber https://files.pythonhosted.org/packages/44/ef/beae4b4ef80902f22e3af073397f079c96969c69b2c7d52a57ea9ae61c9d/retrying-1.3.3.tar.gz
tar -xvf retrying-1.3.3.tar.gz
cd retrying-1.3.3
python3.4 setup.py bdist --formats=rpm
mv dist/retrying-1.3.3-1.noarch.rpm ../RPMs/python-retrying-1.3.3-1.noarch.rpm

