"""Some unit tests, actually these tests are not really strong
it was for me a solution to conduct my development. So don't be affraid :-)
"""

import datetime
import os
import random
import testtools


import warm
from warm import components


#TODO(sahid): Needs isolation

def rndname(n):
    return "%s-%s" % (n, random.randint(0, 9999))

class TestComponents(testtools.TestCase):
    def setUp(self):
        super(TestComponents, self).setUp()
        self.agent = warm.Agent()
        
    def _test_key(self):
        cfg = {"name": rndname("key"),
               "path": "/tmp"}
        key = components.Key(self.agent)(**cfg)
        self.assertTrue(
            os.path.exists("%(path)s/%(name)s.pem" % cfg))
        key.delete()

    def test_volume(self):
        cfg = {"name": rndname("vol"),
               "size": 1}
        vol = components.Volume(self.agent)(**cfg)
        vol.wait_for_ready()
        vol.delete()

    def test_securitygroup(self):
        cfg = {"name": rndname("secgroup"),
               "rules": [
                {"ip_protocol":"tcp",
                 "from_port":"11",
                 "to_port":"11",
                 "cidr": "0.0.0.0/23"},]}
        sec = components.SecurityGroup(self.agent)(**cfg)
        sec.delete()

    def test_server(self):
        cfg = {"name": rndname("srv"),
               "flavor": 1,
               "image": "cirros-0.3.1-x86_64-uec",}
        srv = components.Server(self.agent)(**cfg)
        srv.wait_for_ready()
        srv.delete()

    def test_server_volume(self):
        cfg = {"name": rndname("vol"),
               "size": 1}
        vol = components.Volume(self.agent)(**cfg)

        cfg = {"name": rndname("srv"),
               "flavor": 1,
               "image": "cirros-0.3.1-x86_64-uec"}
        srv = components.Server(self.agent)(**cfg)
        srv.Mount(**{"name": vol.id,
                     "device": "/dev/sdh"})
        
        srv.wait_for_ready()
        srv.delete()
        
        vol.wait_for_ready()
        vol.delete()

    def test_network(self):
        cfg = {"name": rndname("net"),
               "subnets": [
                {"name": rndname("subnet"),
                 "cidr": "10.123.2.0/24",
                 "ip_version": 4},]}
        net = components.Network(self.agent)(**cfg)
        net.delete()

    def test_router(self):
        cfg = {"name": rndname("net")}
        net = components.Network(self.agent)(**cfg)
        
        cfg = {"name": rndname("subnet"),
               "network": net.id,
               "cidr": "10.123.2.0/24",
               "ip_version": 4}
        subnet = components.SubNet(self.agent)(**cfg)

        
        cfg = {"name": rndname("router"),
               #"gateways": [{
               #     "name": rndname("gat"),
               #     "network": net.id},],
               "interfaces": [{
                    "name": rndname("ith"),
                    "subnet": subnet.id},]}
        router = components.Router(self.agent)(**cfg)

        router.delete()
        subnet.delete()
        net.delete()


       

        
        

