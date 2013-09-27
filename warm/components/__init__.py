from openstackclient.common import utils

class Base(object):
    """Base class for a component."""
    def __init__(self, agent, ref=None):
        self._agent = agent
        self._ref = ref
    
    def find(self, id_or_name):
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

        self._ref = utils.find_resource(service, id_or_name)
        return self

    def wait_for_ready(self):
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
                                  success_status=("available", "active"))
        
    def _Execute(self, options):
        raise NotImplemented("This method need to be implemented.")
    
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
            self._agent.client.compute.keypairs.delete(whitelist["name"])
        except:
            pass
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

class SecurityGroup(Base):
    def _Execute(self, options):
        """Handles security groups operations."""
        whitlist = dict(
            name=options["name"],
            description=options.get("description", ""))
        return self._agent.client.compute.security_groups.create(**whitlist)
    
    def _PostExecute(self, options):
        if "rules" in options:
            for rule_opt in options["rules"]:
                self.Rule(**rule_opt)

    def Rule(self, **options):
        options["name"] = self.id
        SecurityGroupRule(self._agent)(**options)
        

class SecurityGroupRule(Base):
    def _Execute(self, options):
        secgrp = SecurityGroup(self._agent).find(options["name"])
        whitelist = dict(
            parent_group_id=secgrp.id,
            ip_protocol=options.get("ip_protocol"), 
            from_port=options.get("from_port"), 
            to_port=options.get("to_port"), 
            cidr=options.get("cidr"))
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
            
        whitelist = dict(
            name=options.get("name"),
            image=image.id,
            flavor=flavor.id,
            security_groups=secgrps
            )
            #userdata=self._UserData(options.get("userdata")),
            #nics=self._Nics(options.get("networks", [])),
            #   )
                
        return self._agent.client.compute.servers.create(**whitelist)

    def _PostExecute(self, options):
        if "volumes" in options:
            #self.wait_for_ready()
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
            label=options["name"], 
            admin_state_up=options.get("admin_state_up", True))
        return self._agent.client.compute.networks.create(**whitelist)


class SubNet(Base):
    def _Execute(self, options):
        network = Network(self._agent).find(options["name"])
        whitlist = dict(
            network_id=network.id,
            name=options.get("name"), 
            cidr=options.get("cidr"), 
            ip_version=options.get("ip_version"), 
            dns_nameservers=options.get("dns_nameservers", []))
        return self.agent.client.compute.networks.create_subnet(**whitlist)


class Router(Base):
    def _Execute(self, options):
        whitelist = dict(
            name=options["name"],
            admin_state_up=options.get("admin_state_up", True))
        return self._agent.clientneutron.create_router({"router": whitelist})

    def PostExecute(self, options):
        if "gateways" in options:
            for gateway_opt in options["gateways"]:
                self._Gateway(**gateway_opt)
        if "interfaces" in options:
            for interface_opt in options["interfaces"]:
                self._Interface(**interface_opt)


class RouterGateway(Base):
    def _Execute(self, options):
        router = Router(self._agent).find(options["name"])
        whitelist = dict(router=router.id,
                         admin_state_up=options.get("admin_state_up", True))
        return self._agent.clientneutron.add_gateway_router(**whitelist)


class RouterInterface(Base):
    def _Execute(self, options):
        router = Router(self._agent).find(options["name"])
        whitlist = dict(router=router.id,
                        admin_state_up=options.get("admin_state_up", True))
        return # needs rpc

