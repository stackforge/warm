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

execfile("warm/version.py")

setuptools.setup(
    name="warm",
    version=__version__,
    author="Sahid Orentino Ferdjaoui (Cloudwatt)",
    author_email="sahid.ferdjaoui@cloudwatt.com",
    description="Deploy a simple OpenStack environment from template",
    long_description=(open(os.path.join(os.getcwd(), "README")).read()),
    license="Apache License 2.0",
    keywords=["openstack", "cloudwatt", "deploy", "cloud"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Environment :: OpenStack",
        ],
    url="https://github.com/sahid/warm.git",
    packages=["warm", "warm.components"],
    install_requires=[
        "requests>=1.1,<1.2.3",
        "six>=1.4.1",
        "distribute",
        "pyyaml",
        "python-openstackclient",
        "python-neutronclient",
        ],
    entry_points="""
        [console_scripts]
        warm = warm:main""",
    )
