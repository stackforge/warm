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

"""Some unit tests, actually these tests are not really strong
it was for me a solution to conduct my development. So don't be affraid :-)
"""

import os
import random
import testtools
import time

import warm
from warm import components


#TODO(sahid): Needs isolation

def rndname(n):
    return "%s-%s" % (n, random.randint(0, 9999))


class TestComponents(testtools.TestCase):
    def setUp(self):
        super(TestComponents, self).setUp()
        self.agent = warm.Agent()

    def test_key(self):
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
                   {"ip_protocol": "tcp",
                    "from_port": "11",
                    "to_port": "11",
                    "cidr": "0.0.0.0/23"}]}
        sec = components.SecurityGroup(self.agent)(**cfg)
        sec.delete()

    def test_server(self):
        cfg = {"name": rndname("srv"),
               "flavor": 1,
               "image": "cirros-0.3.1-x86_64-uec"}
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

    def test_server_network(self):
        cfg = {"name": rndname("net"),
               "subnets": [
                   {"name": rndname("subnet"),
                    "cidr": "10.123.2.0/24",
                    "ip_version": 4}]}
        net = components.Network(self.agent)(**cfg)

        cfg = {"name": rndname("srv"),
               "flavor": 1,
               "image": "cirros-0.3.1-x86_64-uec",
               "networks": [{
                   "name": net.id,
                   "fixed_ip": "10.123.2.10"}]}
        srv = components.Server(self.agent)(**cfg)

        srv.delete()

        time.sleep(5)  # TODO(sahid): Bug, not able to remove an used network
        net.delete()

    def _test_server_userdata(self):
        path = os.path.dirname(os.path.abspath(__file__))
        cfg = {"name": rndname("srv"),
               "flavor": 2,
               "image": "ubuntu",
               "userdata": [path + "/templates/test.ci"]}
        srv = components.Server(self.agent)(**cfg)
        srv.delete()

    def test_network(self):
        cfg = {"name": rndname("net"),
               "subnets": [
                   {"name": rndname("subnet"),
                    "cidr": "10.123.2.0/24",
                    "ip_version": 4}]}
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
                   "subnet": subnet.id}]}
        router = components.Router(self.agent)(**cfg)

        router.delete()
        subnet.delete()
        net.delete()
