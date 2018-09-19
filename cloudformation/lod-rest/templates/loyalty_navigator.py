from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, elasticloadbalancing
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
from troposphere.autoscaling import Tag as AutoScalingTag

class LoyaltyNavigator(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()

        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
        # VpcId is VPC Output
        self.VpcId = self.template.add_parameter(Parameter(
            "VpcId",
            Type="String",
        ))

        #AdminCidrBlock is VPC Output
        self.AdminCidrBlock = self.template.add_parameter(Parameter(
            "AdminCidrBlock",
            Type="String",
        ))

        # RESTPrivSubnet1 is VPC Output
        self.RESTPrivSubnet1 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet1",
            Type="String",
        ))

        # RESTPrivSubnet2 is VPC Output
        self.RESTPrivSubnet2 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet2",
            Type="String",
        ))

        # RESTPubSubnet1 is VPC Output
        self.RESTPubSubnet1 = self.template.add_parameter(Parameter(
            "RESTPubSubnet1",
            Type="String",
        ))

        # RESTPubSubnet2 is VPC Output
        self.RESTPubSubnet2 = self.template.add_parameter(Parameter(
            "RESTPubSubnet2",
            Type="String",
        ))

        self.LoyaltyNavigatorImageId = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorImageId",
            Type="String",
        ))

        self.LoyaltyNavigatorKeyName = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorKeyName",
            Type="String",
        ))

        self.LoyaltyNavigatorInstanceType = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorInstanceType",
            Type="String",
        ))

        self.LoyaltyNavigatorIAMInstanceProfile = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorIAMInstanceProfile",
            Type="String",
        ))

        self.LoyaltyNavigatorASGGroupMinSize = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorASGGroupMinSize",
            Type="String",
        ))

        self.LoyaltyNavigatorASGGroupDesiredSize = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorASGGroupDesiredSize",
            Type="String",
        ))

        self.LoyaltyNavigatorASGGroupMaxSize = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorASGGroupMaxSize",
            Type="String",
        ))

        self.LoyaltyNavigatorASGHealthCheckType = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorASGHealthCheckType",
            Type="String",
        ))

        self.LoyaltyNavigatorASGHealthCheckGracePeriod = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorASGHealthCheckGracePeriod",
            Type="String",
        ))

        self.LoyaltyNavigatorASGCoolDown = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorASGCoolDown",
            Type="String",
        ))


    def add_resources(self):
        self.LoyaltyNavigatorPublicLBSG = self.template.add_resource(ec2.SecurityGroup(
            "LoyaltyNavigatorPublicLBSG",
            GroupDescription="Loadbalancer Security Group For Loyalty Navigator Public LB",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=3389,
                    ToPort=3389,
                    CidrIp=Ref(self.AdminCidrBlock),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    CidrIp=Ref(self.AdminCidrBlock),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyNavigatorPublicLBSG"),
        ))

        self.LoyaltyNavigatorSG = self.template.add_resource(ec2.SecurityGroup(
            "LoyaltyNavigatorSG",
            GroupDescription="Allow communication between Loyalty Navigator Load Balancer and Loyalty NavigatorEc2s",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=3389,
                    ToPort=3389,
                    SourceSecurityGroupId=Ref(self.LoyaltyNavigatorPublicLBSG),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    SourceSecurityGroupId=Ref(self.LoyaltyNavigatorPublicLBSG),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyNavigatorEc2SG"),
        ))

        self.LoyaltyNavigatorPublicLoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "LoyaltyNavigatorPublicLoadBalancer",
            LoadBalancerName=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyNavigatorPubLB",
            Scheme="internet-facing",
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="3389",
                    InstancePort="3389",
                    Protocol="TCP",
                    InstanceProtocol="TCP",
                ),
                elasticloadbalancing.Listener(
                    LoadBalancerPort="80",
                    InstancePort="80",
                    Protocol="HTTP",
                    InstanceProtocol="HTTP",
                )
            ],
            Instances=[],
            SecurityGroups=[Ref(self.LoyaltyNavigatorPublicLBSG)],
            Subnets=[Ref(self.RESTPubSubnet1), Ref(self.RESTPubSubnet2)],
            ConnectionDrainingPolicy=elasticloadbalancing.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=300,
            ),
            CrossZone=True,
            HealthCheck=elasticloadbalancing.HealthCheck(
                Target=Join("", ["TCP:", "3389"]),
                HealthyThreshold="3",
                UnhealthyThreshold="5",
                Interval="10",
                Timeout="5", ),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyNavigatorPubLB"),
        ))

        self.LoyaltyNavigatorLaunchConfiguration = self.template.add_resource(LaunchConfiguration(
            "LoyaltyNavigatorLaunchConfiguration",
            ImageId=Ref(self.LoyaltyNavigatorImageId),
            InstanceType=Ref(self.LoyaltyNavigatorInstanceType),
            IamInstanceProfile=Ref(self.LoyaltyNavigatorIAMInstanceProfile),
            KeyName=Ref(self.LoyaltyNavigatorKeyName),
            SecurityGroups=[Ref(self.LoyaltyNavigatorSG)],
        ))

        self.LoyaltyNavigatorAutoScalingGroup = self.template.add_resource(AutoScalingGroup(
            "LoyaltyNavigatorAutoscalingGroup",
            AutoScalingGroupName=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyNavigatorAutoScalingGroup",
            LaunchConfigurationName=Ref(self.LoyaltyNavigatorLaunchConfiguration),
            LoadBalancerNames=[Ref(self.LoyaltyNavigatorPublicLoadBalancer), Ref(self.LoyaltyNavigatorPublicLoadBalancer)],
            MaxSize=Ref(self.LoyaltyNavigatorASGGroupMaxSize),
            MinSize=Ref(self.LoyaltyNavigatorASGGroupMinSize),
            DesiredCapacity=Ref(self.LoyaltyNavigatorASGGroupDesiredSize),
            HealthCheckType=Ref(self.LoyaltyNavigatorASGHealthCheckType),
            HealthCheckGracePeriod=Ref(self.LoyaltyNavigatorASGHealthCheckGracePeriod),
            Cooldown=Ref(self.LoyaltyNavigatorASGCoolDown),
            VPCZoneIdentifier=[Ref(self.RESTPrivSubnet1), Ref(self.RESTPrivSubnet2)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyNavigator-Ec2", True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientEnvironmentKey"], True),
            ],
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "LoyaltyNavigatorEC2SecurityGroup",
            Value=Ref(self.LoyaltyNavigatorSG),
        ))

def sceptre_handler(sceptre_user_data):
    loyaltynavigator = LoyaltyNavigator(sceptre_user_data)
    return loyaltynavigator.template.to_json()
