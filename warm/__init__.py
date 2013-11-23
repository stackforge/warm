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

"""The main script of the project."""

import logging
import optparse
import os
import yaml
import sys

from openstackclient.common import clientmanager
from neutronclient.neutron import client as neutron #TODO(sahid): Needs to remove.

from warm import components

DEFAULT_LOGFILE = "/dev/null"
DEFAULT_LOGLEVEL = logging.DEBUG
DEFAULT_COMPUTE_API_VERSION = '2'
DEFAULT_IDENTITY_API_VERSION = '2.0'
DEFAULT_IMAGE_API_VERSION = '2'
DEFAULT_OBJECT_API_VERSION = '1'
DEFAULT_VOLUME_API_VERSION = '1'
DEFAULT_DOMAIN = 'default'

OS_USERNAME = os.getenv("OS_USERNAME")
OS_PASSWORD = os.getenv("OS_PASSWORD")
OS_TENANT_NAME = os.getenv("OS_TENANT_NAME")
OS_AUTH_URL = os.getenv("OS_AUTH_URL")

USAGE = "usage: %prog <template> [options]"

class Agent(object):
    def __init__(self, **options):
        self.options = options

        self.api_version = {
            'compute': self.options.get(
                "compute_api_version", DEFAULT_COMPUTE_API_VERSION),
            'identity': self.options.get(
                "identity_api_version", DEFAULT_IDENTITY_API_VERSION),
            'image': self.options.get(
                "image_api_version", DEFAULT_IMAGE_API_VERSION),
            'object-store': self.options.get(
                "object_api_version", DEFAULT_OBJECT_API_VERSION),
            'volume': self.options.get(
                "volume_api_version", DEFAULT_VOLUME_API_VERSION),
            }
        
        self.client = clientmanager.ClientManager(
            token=self.options.get("token"),
            url=self.options.get("url"),
            auth_url=self.options.get("auth_url", OS_AUTH_URL),
            project_name=self.options.get("project_name", OS_TENANT_NAME),
            project_id=self.options.get("project_id"),
            username=self.options.get("username", OS_USERNAME),
            password=self.options.get("password", OS_PASSWORD),
            region_name=self.options.get("region_name"),
            api_version=self.api_version)

        self.clientneutron = neutron.Client(
            token=self.options.get("token"),
            username=self.options.get("username", OS_USERNAME),
            password=self.options.get("password", OS_PASSWORD),
            tenant_name=self.options.get("project_name", OS_TENANT_NAME),
            auth_url=self.options.get("auth_url", OS_AUTH_URL),
            region_name=self.options.get("region_name"),
            insecure=self.options.get("insecure", True),
            api_version=self.options.get("api_version", "2.0"))

        
    def _InitKeypairs(self):
        logging.info("Initializing keypairs...")
        self.key_name = self.options.get("key_name", DEFAULT_KEY_NAME)
        try:
            self.client.compute.keypairs.delete(key_name)
        except:
            pass
        key = self.client.compute.keypairs.create(key_name)
        f = open("%s.pem" % self.key_name, 'w')
        f.write(key.private_key)
        f.close

def main():   
    parser = optparse.OptionParser(usage=USAGE)
    parser.add_option("-V", "--verbose", 
                      dest="verbose",
                      action="store_true",
                      help="Be more verbose.",
                      default=False)
    parser.add_option("-v", "--version", 
                      dest="version",
                      action="store_true",
                      help="Print the current version used.",
                      default=False)
    
    (options, args) = parser.parse_args()

    verbose = getattr(options, "verbose")
    out = DEFAULT_LOGFILE
    if verbose:
        out = "/dev/stdout"
    logging.basicConfig(filename=out, level=DEFAULT_LOGLEVEL)

    if getattr(options, "version"):
        print __version__
        exit()

    if len(sys.argv) < 2:
        parser.print_help()
        exit()
    
    stream = file(sys.argv[1])
    config = yaml.load(stream)

    agent = Agent(**config)

    for key, cls in CLASS_MAPPING: 
        if key in config:
            logging.debug("Some %s configurations found, work in progress..." % key)
            for cfg in config[key]:
                getattr(components, cls)(agent)(**cfg)

CLASS_MAPPING=[
    ("key", "Key"),
    ("volume", "Volume"),
    ("network", "Network"),
    ("subnet", "SubNet"),
    ("router", "Router"),
    ("securitygroup", "SecurityGroup"),
    ("securitygrouprule", "SecurityGroupRule"),
    ("server", "Server"),
]

if __name__ == "__main__":
    main()
