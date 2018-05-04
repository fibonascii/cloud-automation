from base import BaseCloudFormation
from troposphere import ec2, Ref, Parameter, Output, elasticloadbalancing, autoscaling

class Instances(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
        self.Slave = False

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
        
        self.ScaleCapacity = self.template.add_parameter(Parameter(
            "ScaleCapacity",
            Default="1",
            Type="String",
            Description="Number of servers to run in scale group",
        ))

        self.AMIID = self.template.add_parameter(Parameter(
            "AMIID",
            Type="String",
        ))

        self.availability_zone1 = self.template.add_parameter(Parameter(
            "AvailabilityZone1",
            Type="String",
        ))

        self.availability_zone2 = self.template.add_parameter(Parameter(
            "AvailabilityZone2",
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


    def add_resources(self):
        self.LoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "LoadBalancer",
            ConnectionDrainingPolicy=elasticloadbalancing.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=120,
                ),
            Subnets=[Ref(self.PublicSubnet1)],
            HealthCheck=elasticloadbalancing.HealthCheck(
                Target="HTTP:80/",
                HealthyThreshold="5",
                UnhealthyThreshold="2",
                Interval="20",
                Timeout="15",
                ),
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="443",
                    InstancePort="80",
                    Protocol="HTTPS",
                    InstanceProtocol="HTTP",
                    ),
                ],
            CrossZone=True,
            SecurityGroups=[Ref(self.LoadBalancerSecurityGroup)],
            LoadBalancerName=Ref(self.LoadBalancerName),
            Scheme="internet-facing",
         ))

        self.instance = self.template.add_resource(ec2.Instance(
            "JenkinsInstance",
            ImageId=Ref(self.AMIID),
            InstanceType="m1.small",
            Tags=self.default_tags,
            KeyName=Ref(self.KeyPair),
            NetworkInterfaces=[
               ec2.NetworkInterfaceProperty(
                GroupSet=[
                    Ref(self.PrivateSubnet1)],
                AssociatePublicIpAddress='false',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(self.PrivateSubnet1))],
                ))
        if self.Slave == True:
            self.LaunchConfiguration = self.template.add_resource(autoscaling.LaunchConfiguration(
                "LaunchConfiguration",
                ImageId=Ref(self.AMIID),
                SecurityGroups=[Ref(self.LoadBalancerSecurityGroup)],
                BlockDeviceMappings=[
                    ec2.BlockDeviceMapping(
                        DeviceName="/dev/sda1",
                        Ebs=ec2.EBSBlockDevice(
                            VolumeSize="50"
                            )
                        ),
                    ],
                InstanceType="m1.small",
                ))
            

            self.AutoScalingGroup = self.template.add_resource(autoscaling.AutoScalingGroup(
                "AutoScalingGroup",
               DesiredCapacity=Ref(self.ScaleCapacity),
               Tags=self.default_tags,
               LaunchConfigurationName=Ref(self.LaunchConfiguration),
               MinSize=Ref(self.ScaleCapacity),
               MaxSize=Ref(self.ScaleCapacity),
               LoadBalancerNames=[Ref(self.LoadBalancer)],
               AvailabilityZones=[Ref(self.availability_zone1), Ref(self.availability_zone2)],
               HealthCheckType="EC2",
               ))
           

    def add_outputs(self):
        return

def sceptre_handler(sceptre_user_data):
    instances = Instances(sceptre_user_data)
    return instances.template.to_json()
