
import logging
import optparse
import os
import yaml

from openstackclient.common import clientmanager
from neutronclient.neutron import client as neutron #TODO(sahid): Needs to remove.

from warm import components

DEFAULT_CFGFILE = "config.yaml"
DEFAULT_LOGFILE = "/dev/stdout"#"warm.log"
DEFAULT_LOGLEVEL = logging.DEBUG
DEFAULT_COMPUTE_API_VERSION = '2'
DEFAULT_IDENTITY_API_VERSION = '2.0'
DEFAULT_IMAGE_API_VERSION = '2'
DEFAULT_OBJECT_API_VERSION = '1'
DEFAULT_VOLUME_API_VERSION = '1'
DEFAULT_DOMAIN = 'default'
DEFAULT_KEY_NAME = 'my'

OS_USERNAME = os.getenv("OS_USERNAME")
OS_PASSWORD = os.getenv("OS_PASSWORD")
OS_TENANT_NAME = os.getenv("OS_TENANT_NAME")
OS_AUTH_URL = os.getenv("OS_AUTH_URL")

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
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", 
                      dest="config",
                      help="Uses a custom config file.", 
                      metavar="FILE",
                      default=DEFAULT_CFGFILE)
    parser.add_option("-l", "--logfile", 
                      dest="logfile",
                      help="Uses a custom log file (ex: stdout).", 
                      metavar="FILE",
                      default=DEFAULT_LOGFILE)
    
    (options, args) = parser.parse_args()

    cfgfile = getattr(options, "config")
    logfile = getattr(options, "logfile")

    logging.basicConfig(filename=logfile, level=DEFAULT_LOGLEVEL)
    
    stream = file(cfgfile)
    config = yaml.load(stream)

    agent = Agent(**config)

    for key, cls in CLASS_MAPPING: 
        if key in config:
            logging.debug("Some %s configurations found, work in progress..." % key)
            for cfg in config[key]:
                getattr(components, cls)(agent)(**cfg)

CLASS_MAPPING=[
    ("key", "Key"),
    ("securitygroup", "SecurityGroup"),
    ("securitygrouprule", "SecurityGroupRule"),
    ("volume", "Volume"),
    ("server", "Server"),
#    ("network", "Network"),
#    ("subnet", "SubNet"),
#    ("router", "Router"),
]

if __name__ == "__main__":
    main()
