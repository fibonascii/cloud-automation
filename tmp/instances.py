from base import BaseCloudFormation
from troposphere import ec2, Ref, Parameter, Output, elasticloadbalancing, Tags, GetAtt


class Instances(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):

        self.LoadBalancerName = self.template.add_parameter(Parameter(
            "LoadBalancerName",
            Default=self.environment_name + "-LOADBALANCER-1",
            Type="String",
            Description="Name of Development Load Balancer",
        ))

        self.SlaveLoadBalancerName = self.template.add_parameter(Parameter(
            "SlaveLoadBalancerName",
            Default=self.environment_name + "-SLAVELB",
            Type="String",
            Description="Name of Slave Development Load Balancer"
        ))

        self.LoadBalancerSecurityGroup = self.template.add_parameter(Parameter(
            "LoadBalancerSecurityGroup",
            Type="String",
            Description="SecurityGroup for Development LoadBalancer",
        ))
        
        self.AMIID = self.template.add_parameter(Parameter(
            "AMIID",
            Default="ami-bb8209ad",
            Type="String",
        ))

        self.SLAVEAMIID = self.template.add_parameter(Parameter(
            "SLAVEAMIID",
            Default="ami-27003e42",
            Type="String",
        ))

        self.AvailabilityZoneA = self.template.add_parameter(Parameter(
            "AvailabilityZoneA",
            Type="String",
        ))

        self.AvailabilityZoneB = self.template.add_parameter(Parameter(
            "AvailabilityZoneB",
            Type="String",
        ))

        self.PublicSubnet1 = self.template.add_parameter(Parameter(
            "PublicSubnet1",
            Type="String",
        ))

        self.PrivateSubnet1 = self.template.add_parameter(Parameter(
            "PrivateSubnet1",
            Type="String",
        ))

        self.KeyPair = self.template.add_parameter(Parameter(
            "KeyPair",
            Type="String",
        ))

        self.InstanceSecurityGroup = self.template.add_parameter(Parameter(
            "InstanceSecurityGroup",
            Type="String",
        ))

        self.SlaveInstanceSecurityGroup = self.template.add_parameter(Parameter(
            "SlaveInstanceSecurityGroup",
            Type="String",
        ))

    def add_resources(self):
        self.master_instance = self.template.add_resource(ec2.Instance(
            "JenkinsInstance",
            ImageId=Ref(self.AMIID),
            InstanceType="t2.micro",
            Tags=self.default_tags + Tags(
                                       Name=self.environment_name + "-MASTERINSTANCE"),
            KeyName=Ref(self.KeyPair),
            SecurityGroupIds=[Ref(self.InstanceSecurityGroup)],
            SubnetId=Ref(self.PrivateSubnet1),
            AvailabilityZone=Ref(self.AvailabilityZoneA),
        ))

        self.master_loadbalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "LoadBalancer",
            ConnectionDrainingPolicy=elasticloadbalancing.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=120,
                ),
            Subnets=[Ref(self.PublicSubnet1)],
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="80",
                    InstancePort="8080",
                    Protocol="tcp",
                    InstanceProtocol="tcp",
                    ),
                elasticloadbalancing.Listener(
                    LoadBalancerPort="22",
                    InstancePort="22",
                    Protocol="tcp",
                    InstanceProtocol="tcp",
                    ),
                ],
            CrossZone=True,
            SecurityGroups=[Ref(self.LoadBalancerSecurityGroup)],
            LoadBalancerName=Ref(self.LoadBalancerName),
            Scheme="internet-facing",
            Instances=[Ref(self.master_instance)],
         ))

    def add_outputs(self):
        return


def sceptre_handler(sceptre_user_data):
    instances = Instances(sceptre_user_data)
    return instances.template.to_json()
