from base import BaseCloudFormation
from troposphere import ec2, Ref, Parameter, Output, elasticloadbalancing, autoscaling

class Instances(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):

        self.LoadBalancerName = self.template.add_parameter(Parameter(
            "LoadBalancerName",
            Default="DevLoadBalancer",
            Type="String",
            Description="Name of Development Load Balancer",
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

        self.availability_zone1 = self.template.add_parameter(Parameter(
            "AvailabilityZone1",
            Type="String",
            Default="us-east-1a",
        ))

        self.availability_zone2 = self.template.add_parameter(Parameter(
            "AvailabilityZone2",
            Type="String",
            Default="us-east-1-b",
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


    def add_resources(self):
        self.instance = self.template.add_resource(ec2.Instance(
            "JenkinsInstance",
            ImageId=Ref(self.AMIID),
            InstanceType="t2.micro",
            Tags=self.default_tags,
            KeyName=Ref(self.KeyPair),
            SecurityGroupIds=[Ref(self.InstanceSecurityGroup)],
            SubnetId=Ref(self.PrivateSubnet1),

            AvailabilityZone="us-east-1a",
                ))


        self.LoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "LoadBalancer",
            ConnectionDrainingPolicy=elasticloadbalancing.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=120,
                ),
            Subnets=[Ref(self.PublicSubnet1)],
            #HealthCheck=elasticloadbalancing.HealthCheck(
            #    Target="TCP:22/",
            #    HealthyThreshold="5",
            #    UnhealthyThreshold="2",
            #    Interval="20",
            #    Timeout="15",
            #    ),
            Listeners=[
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
            Instances=[Ref(self.instance)],
         ))


    def add_outputs(self):
        return

def sceptre_handler(sceptre_user_data):
    instances = Instances(sceptre_user_data)
    return instances.template.to_json()
