#   Copyright 2013 Cloudwatt 
#   
#   Author: Sahid Orentino Ferdjaoui <sahid.ferdjaoui@cloudwatt.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import os
import setuptools


def read(*rnames):
    return open(os.path.join(os.getcwd(), *rnames)).read()


setuptools.setup(
    name='warm',
    version=read('VERSION').strip(),
    author="Sahid Orentino Ferdjaoui",
    author_email="sahid.ferdjaoui@cloudwatt.com",
    description="Warm - To deploy a simple OpenStack environment from template",
    long_description=(read('README')),
    license="Apache License 2.0",
    keywords=["openstack",],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Environment :: OpenStack',
        ],
    url='https://github.com/sahid/warm.git',
    packages=setuptools.find_packages('warm'),
    include_package_data=False,
    package_dir={'': 'warm'},
    data_files=[('templates', ['templates/config.yaml.sample'])],
    install_requires=[
        'python-openstackclient',
        'python-neutronclient',
        ],
    entry_points="""
        [console_scripts]
        warm = warm:main""",
    zip_safe=False,
    )
