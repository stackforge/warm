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

"""Components."""

import os
import uuid

from openstackclient.common import utils, exceptions
from neutronclient.neutron import v2_0 as neutronV20


class Base(object):
    """Base class for a component."""
    def __init__(self, agent, ref=None):
        self._agent = agent
        self._ref = ref
    
    def find(self, id_or_name):
        service = None
        if isinstance(self, Key):
            service = self._agent.client.compute.keypairs
        if isinstance(self, Image):
            service = self._agent.client.compute.images
        elif isinstance(self, Server):
            service = self._agent.client.compute.servers
        elif isinstance(self, Flavor):
            service = self._agent.client.compute.flavors
        elif isinstance(self, Volume):
            service = self._agent.client.volume.volumes
        elif isinstance(self, SecurityGroup):
            service = self._agent.client.compute.security_groups
        elif isinstance(self, Network):
            service = self._agent.client.compute.networks
        elif isinstance(self, SubNet):
            sid = neutronV20.find_resourceid_by_name_or_id(
                self._agent.clientneutron, "subnet", id_or_name)
            self._ref = self._agent.clientneutron.show_subnet(sid)
        elif isinstance(self, Router):
            rid = neutronV20.find_resourceid_by_name_or_id(
                self._agent.clientneutron, "router", id_or_name)
            self._ref = self._agent.clientneutron.show_router(rid)
            
        if service:
            self._ref = utils.find_resource(service, id_or_name)
        return self

    def wait_for_ready(self, field="status", success=("available", "active")):
        if isinstance(self, Image):
            service = self._agent.client.compute.images
        elif isinstance(self, Server):
            service = self._agent.client.compute.servers
        elif isinstance(self, Flavor):
            service = self._agent.client.compute.flavors
        elif isinstance(self, Volume):
            service = self._agent.client.volume.volumes

        utils.wait_for_status(service.get, 
                              self.id, 
                              sleep_time=1, 
                              success_status=success,
                              status_field=field)

    def delete(self):
        if not self._ref:
            raise Exception("This component is not initialize yet.")
        return self._Delete()

        
    def _Execute(self, options):
        raise NotImplemented("This method needs to be implemented.")

    def _Delete(self):
        return self._ref.delete()
    
    def _PostExecute(self, options):
        pass

    def _Id(self):
        return self._ref.id

    def _Name(self):
        return self._ref.name

    def __call__(self, **options):
        self._ref = self._Execute(options)
        self._PostExecute(options)
        return self
    
    @property
    def id(self):
        if not self._ref:
            raise Exception("This component is not initialize yet.")
        return self._Id()

    @property
    def name(self):
        if not self._ref:
            raise Exception("This component is not initialize yet.")
        return self._Name()

class Key(Base):
    """Handles keypairs operations."""
    def _Execute(self, options):
        whitelist = dict(
            name=options["name"],
            path=options.get("path", "."))
        try:
            key = self.find(whitelist["name"])
        except exceptions.CommandError:
            key = self._agent.client.compute.keypairs.create(whitelist["name"])
            f = open("%(path)s/%(name)s.pem" % whitelist, 'w')
            f.write(key.private_key)
            f.close
        return key

class Image(Base):
    """Handles image operations."""
    pass


class Flavor(Base):
    """Handles flavor operations."""
    pass


class Volume(Base):
    """Handles volume operations."""
    def _Execute(self, options):
        whitelist = dict(
            size=options["size"],
            display_name=options.get("name", ""))
        return self._agent.client.volume.volumes.create(**whitelist)

    def _Name(self):
        return self._ref.display_name

class SecurityGroup(Base):
    def _Execute(self, options):
        """Handles security groups operations."""
        whitelist = dict(
            name=options["name"],
            description=options.get("description", "<empty>"))
        return self._agent.client.compute.security_groups.create(**whitelist)
    
    def _PostExecute(self, options):
        if "rules" in options:
            for rule_opt in options["rules"]:
                self.Rule(**rule_opt)

    def Rule(self, **options):
        options["group"] = self.id
        SecurityGroupRule(self._agent)(**options)
        

class SecurityGroupRule(Base):
    def _Execute(self, options):
        parent = SecurityGroup(self._agent).find(options["group"])
        group_id=None
        if "secgroup" in options:
            group = SecurityGroup(self._agent).find(options["secgroup"])
            if group:
                group_id = group.id
        whitelist = dict(
            parent_group_id=parent.id,
            ip_protocol=options.get("ip_protocol"), 
            from_port=options.get("from_port"), 
            to_port=options.get("to_port"), 
            cidr=options.get("cidr"),
            group_id=group_id)
        return self._agent.client.compute.security_group_rules.create(**whitelist)

class Server(Base):
    """Handle server (instance) operations."""
    def _Execute(self, options):
        image = Image(self._agent).find(options.get("image"))
        flavor = Flavor(self._agent).find(options.get("flavor"))

        secgrps = [] # TODO(sahid): utiliser un map?
        for name in options.get("securitygroups", []):
            secgrp = SecurityGroup(self._agent).find(name)
            secgrps.append(secgrp.id)

        networks = []
        for obj in options.get("networks", []):
            net = Network(self._agent).find(obj["name"])
            networks.append({
                    "net-id": net.id,
                    "v4-fixed-ip": obj.get("fixed_ip"),
                    "port-id": obj.get("port"),
                    })

        userdata = None
        if "userdata" in options:
            tmpname = uuid.uuid1()
            os.system("/usr/bin/write-mime-multipart --output=/tmp/%s %s " % 
                      (tmpname, " ".join(options["userdata"])))
            userdata = open("/tmp/%s" % tmpname)
            
        whitelist = dict(
            name=options.get("name"),
            image=image.id,
            flavor=flavor.id,
            security_groups=secgrps,
            nics=networks,
            userdata=userdata,
            availability_zone=options.get("availability_zone"),
            key_name=options.get("key"),
            min_count=options.get("min_count"),
            max_count=options.get("max_count"))

        return self._agent.client.compute.servers.create(**whitelist)

    def _PostExecute(self, options):
        if "volumes" in options:
            self.wait_for_ready()
            for volume_opt in options["volumes"]:
                self.Mount(**volume_opt)
                
    def Mount(self, **options):
        volume = Volume(self._agent).find(options["name"])
        volume.wait_for_ready()
        whitelist = dict(
            server_id=self.id,
            volume_id=volume.id,
            device=options["device"])
        self._agent.client.compute.volumes.create_server_volume(**whitelist)

class Network(Base):
    def _Execute(self, options):
        whitelist = dict(
            name=options["name"], 
            admin_state_up=options.get("admin_state_up", True),
            )
        body = {"network": whitelist}
        #TODO(sahid): Needs to use client.
        return self._agent.clientneutron.create_network(body)

    def _PostExecute(self, options):
        if "subnets" in options:
            for cfg in options["subnets"]:
                self.AttachSubNet(cfg)

    def AttachSubNet(self, options):
        options["network"] = self.id
        SubNet(self._agent)(**options)

    def _Id(self):
        if isinstance(self._ref, dict):
            return self._ref["network"]["id"]
        return self._ref.id

    def _Name(self):
        if isinstance(self._ref, dict):
            return self._ref["network"]["name"]
        return self._ref.name

    def _Delete(self):
        if isinstance(self._ref, dict):
            return self._agent.clientneutron.delete_network(self.id)
        return self.delete()


class SubNet(Base):
    def _Execute(self, options):
        network = Network(self._agent).find(options["network"])
        whitelist = dict(
            network_id=network.id,
            name=options.get("name"), 
            cidr=options.get("cidr"), 
            ip_version=options.get("ip_version"), 
            dns_nameservers=options.get("dns_nameservers", []))
        body = {"subnet": whitelist}
        #TODO(sahid): Needs to use client.
        return self._agent.clientneutron.create_subnet(body)

    def _Id(self):
        if isinstance(self._ref, dict):
            return self._ref["subnet"]["id"]
        return self._ref.id

    def _Name(self):
        if isinstance(self._ref, dict):
            return self._ref["subnet"]["name"]
        return self._ref.name

    def _Delete(self):
        if isinstance(self._ref, dict):
            return self._agent.clientneutron.delete_subnet(self.id)
        self._ref.delete()


class Router(Base):
    def _Execute(self, options):
        whitelist = dict(
            name=options["name"],
            admin_state_up=options.get("admin_state_up", True))
        return self._agent.clientneutron.create_router({"router": whitelist})

    def _PostExecute(self, options):
        if "gateways" in options:
            for gateway_opt in options["gateways"]:
                self.AttachGateway(gateway_opt)
        if "interfaces" in options:
            for interface_opt in options["interfaces"]:
                self.AttachInterface(interface_opt)

    def AttachInterface(self, options):
        options["router"] = self.id
        RouterInterface(self._agent)(**options)

    def AttachGateway(self, options):
        options["router"] = self.id
        RouterGateway(self._agent)(**options)

    def _Id(self):
        if isinstance(self._ref, dict):
            return self._ref["router"]["id"]
        return self._ref.id

    def _Name(self):
        if isinstance(self._ref, dict):
            return self._ref["router"]["name"]
        return self._ref.name

    def _Delete(self):
        if isinstance(self._ref, dict):
            for name, interfaces in self._agent.clientneutron.list_ports().items():
                for interface in interfaces:
                    if interface["device_id"] == self.id:
                        RouterInterface(self._agent, interface).delete()
            return self._agent.clientneutron.delete_router(self.id)
        
        self._ref.delete()


class RouterInterface(Base):
    def _Execute(self, options):
        router = Router(self._agent).find(options["router"])
        subnet = SubNet(self._agent).find(options["subnet"])
        whitelist = dict(
            name = options.get("name"),
            subnet_id=subnet.id,
            )
        return self._agent.clientneutron.add_interface_router(
            router.id, whitelist)

    def _Id(self):
        if isinstance(self._ref, dict):
            return self._ref["id"]
        return self._ref.id

    def _Name(self):
        if isinstance(self._ref, dict):
            return self._ref["name"]
        return self._ref.name

    def _Delete(self):
        if isinstance(self._ref, dict):
            return self._agent.clientneutron.remove_interface_router(
                self._ref["device_id"], 
                {"subnet_id":self._ref["fixed_ips"][0]['subnet_id']})
        self._ref.delete()


class RouterGateway(Base):
    def _Execute(self, options):
        router = Router(self._agent).find(options["router"])
        network = Network(self._agent).find(options["network"])
        whitelist = dict(
            name = options.get("name"),
            network_id=network.id,
            )
        return self._agent.clientneutron.add_gateway_router(
            router.id, whitelist)

    def _Id(self):
        if isinstance(self._ref, dict):
            return self._ref["id"]
        return self._ref.id

    def _Name(self):
        if isinstance(self._ref, dict):
            return self._ref["name"]
        return self._ref.name

    def _Delete(self):
        if isinstance(self._ref, dict):
            return self._agent.clientneutron.remove_gateway_router(
                self._ref["device_id"], 
                {"network_id":self._ref["fixed_ips"][0]['subnet_id']})
        self._ref.delete()



