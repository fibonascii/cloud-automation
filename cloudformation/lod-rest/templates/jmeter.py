from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, elasticloadbalancing
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, LifecycleHookSpecification
from troposphere.autoscaling import Tag as AutoScalingTag
from troposphere.ssm import Parameter as SSMParameter


class JMeter(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):

        self.AdminCidrBlock = self.template.add_parameter(Parameter(
            "AdminCidrBlock",
            Type="String",
            Description="The Cidr Block of the Administrator for Access Purposes",
        ))

        self.JmeterMasterImageId = self.template.add_parameter(Parameter(
            "JmeterMasterImageId",
            Type="String",
        ))

        self.JMeterSlaveImageId = self.template.add_parameter(Parameter(
            "JMeterSlaveImageId",
            Type="String",
        ))

        self.SlaveCount = self.template.add_parameter(Parameter(
            "SlaveCount",
            Type="String",
        ))

        self.ServerKeyName = self.template.add_parameter(Parameter(
            "ServerKeyName",
            Type="String",
        ))

        self.IAMInstanceProfile = self.template.add_parameter(Parameter(
            "IAMInstanceProfile",
            Type="String",
            Description="The IAM Instance Profile",
        ))

        self.MasterInstanceType = self.template.add_parameter(Parameter(
            "MasterInstanceType",
            Type="String",
            Description="The Instance Type",
        ))

        self.SlaveInstanceType = self.template.add_parameter(Parameter(
            "SlaveInstanceType",
            Type="String",
            Description="The Instace Type",
        ))

        self.SlaveRequested = self.template.add_parameter(Parameter(
            "SlaveRequested",
            Type="String",
            Description="The Slave Requested Flag",
        ))

        self.VpcId = self.template.add_parameter(Parameter(
            "VpcId",
            Type="String",
            Description="The VPC ID From the VPC Stack",
            ))

        self.RESTPubSubnet1 = self.template.add_parameter(Parameter(
            "RESTPubSubnet1",
            Type="String",
            Description="RESTPubSubnet1 Output from VPC Stack",
            ))

        self.RESTPubSubnet2 = self.template.add_parameter(Parameter(
            "RESTPubSubnet2",
            Type="String",
            Description="RESTPubSubnet2 Output from VPC Stack",
            ))

        self.RESTPrivSubnet1 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet1",
            Type="String",
            Description="RESTPrivSubnet1 Output from VPC Stack",
            ))

        self.RESTPrivSubnet2 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet2",
            Type="String",
            Description="RESTPrivSubnet2 Output from VPC Stack",
            ))

        self.TestExecutionLengthSSMParameterValue = self.template.add_parameter(Parameter(
            "TestExecutionLengthSSMParameterValue",
            Type="String",
            Description="SSM Parameter for the Execution Length of the test",
        ))

        self.JMXFileNameSSMParameterValue = self.template.add_parameter(Parameter(
            "JMXFileNameSSMParameterValue",
            Type="String",
            Description="The Name of the JMX File Stored in S3",
        ))

        self.S3JMXFileLocationSSMParameterValue = self.template.add_parameter(Parameter(
            "S3JMXFileLocationSSMParameterValue",
            Type="String",
            Description="The Location of the JMX File Stored in S3",
        ))

        self.JMXResultsFileNameSSMParameterValue = self.template.add_parameter(Parameter(
            "JMXResultsFileNameSSMParameterValue",
            Type="String",
            Description="The Name of the JMX Results File",
        ))


    def add_resources(self):
        self.MasterPublicLBSG = self.template.add_resource(ec2.SecurityGroup(
            "MasterPublicLBSG",
            GroupDescription="Loadbalancer SG For Jmeter Public",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    CidrIp=Ref(self.AdminCidrBlock),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterMasterPublicLBSG"),
        ))

        self.MasterEc2SG = self.template.add_resource(ec2.SecurityGroup(
            "MasterEc2SG",
            GroupDescription="Allow communication between Rest Api Load Balancers and Rest Api Ec2s",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.MasterPublicLBSG),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterMasterEC2InstanceSG"),
        ))

        self.SlavePrivateLBSG = self.template.add_resource(ec2.SecurityGroup(
            "SlavePrivateLBSG",
            GroupDescription="Security Group for Private JMeter Slave Load Balancer",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.MasterEc2SG),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=24000,
                    ToPort=26999,
                    SourceSecurityGroupId=Ref(self.MasterEc2SG),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterSlavePrivateLBSG"),

        ))

        self.SlaveEc2SG = self.template.add_resource(ec2.SecurityGroup(
            "SlaveEc2SG",
            GroupDescription="Security Group for Private JMeter Slave Load Balancer",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.SlavePrivateLBSG),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.MasterEc2SG),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=24000,
                    ToPort=26999,
                    SourceSecurityGroupId=Ref(self.SlavePrivateLBSG),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterSlaveEC2InstanceSG"),
        ))

        self.SlaveSGInterNodeCommunicationIngress = self.template.add_resource(ec2.SecurityGroup(
            "SlaveSGInterNodeCommunicationIngress",
            GroupDescription="Security Group for Private JMeter Slave Load Balancer",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.SlaveEc2SG),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterSlaveNodeCommuncationSG"),

        ))

        self.MasterPublicLoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "MasterPublicLoadBalancer",
            LoadBalancerName=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterMasterPubELB",
            Scheme="internet-facing",
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="22",
                    InstancePort="22",
                    Protocol="TCP",
                    InstanceProtocol="TCP"
                )
            ],
            Instances=[],
            SecurityGroups=[Ref(self.MasterPublicLBSG)],
            Subnets=[Ref(self.RESTPubSubnet1)],
            CrossZone=True,
            HealthCheck=elasticloadbalancing.HealthCheck(
                Target=Join("", ["TCP:", "22"]),
                HealthyThreshold="3",
                UnhealthyThreshold="10",
                Interval="10",
                Timeout="5", ),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterMasterPublicLB"),

        ))

        self.SlavePrivateLoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "SlavePrivateLoadBalancer",
            LoadBalancerName=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterSlavePubELB",
            Scheme="internal",
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="22",
                    InstancePort="22",
                    Protocol="TCP",
                    InstanceProtocol="TCP"
                )
            ],
            Instances=[],
            SecurityGroups=[Ref(self.SlavePrivateLBSG)],
            Subnets=[Ref(self.RESTPrivSubnet1)],
            CrossZone=True,
            HealthCheck=elasticloadbalancing.HealthCheck(
                Target=Join("", ["TCP:", "22"]),
                HealthyThreshold="3",
                UnhealthyThreshold="10",
                Interval="10",
                Timeout="5", ),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterSlavePrivateLB"),

        ))

        self.MasterLaunchConfiguration = self.template.add_resource(LaunchConfiguration(
            "MasterLaunchConfiguration",
            ImageId=Ref(self.JmeterMasterImageId),
            InstanceType=Ref(self.MasterInstanceType),
            IamInstanceProfile=Ref(self.IAMInstanceProfile),
            KeyName=Ref(self.ServerKeyName),
            SecurityGroups=[Ref(self.MasterEc2SG)],
        ))

        self.MasterAutoScalingGroup = self.template.add_resource(AutoScalingGroup(
            "MasterAutoScaling",
            AutoScalingGroupName=self.environment_parameters[
                                     "ClientEnvironmentKey"] + "-JMeterMasterAutoScalingGroup",
            LaunchConfigurationName=Ref(self.MasterLaunchConfiguration),
            LoadBalancerNames=[Ref(self.MasterPublicLoadBalancer)],
            MaxSize="1",
            MinSize="1",
            DesiredCapacity="1",
            VPCZoneIdentifier=[Ref(self.RESTPubSubnet1), Ref(self.RESTPubSubnet2)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-JMeterMasterEC2", True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientCode"], True),
                ],
        ))

        self.SlaveLaunchConfiguration = self.template.add_resource(LaunchConfiguration(
            "SlaveLaunchConfiguration",
            ImageId=Ref(self.JMeterSlaveImageId),
            InstanceType=Ref(self.SlaveInstanceType),
            IamInstanceProfile=Ref(self.IAMInstanceProfile),
            KeyName=Ref(self.ServerKeyName),
            SecurityGroups=[Ref(self.SlaveEc2SG)],
        ))

        self.SlaveAutoScalingGroup = self.template.add_resource(AutoScalingGroup(
            "SlaveAutoScaling",
            AutoScalingGroupName=self.environment_parameters[
                                     "ClientEnvironmentKey"] + "JMeterSlaveAutoScalingGroup",
            LaunchConfigurationName=Ref(self.SlaveLaunchConfiguration),
            LoadBalancerNames=[Ref(self.SlavePrivateLoadBalancer)],
            MaxSize="1",
            MinSize="1",
            DesiredCapacity="1",
            VPCZoneIdentifier=[Ref(self.RESTPrivSubnet1), Ref(self.RESTPrivSubnet2)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-JMeterSlaveEC2", True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientCode"], True),
                ],
        ))

        self.TestExecutionLengthSSMParameter = self.template.add_resource(SSMParameter(
            "TestExecutionLengthSSMParameter",
            Description="The length of time the JMeter Test can Run",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterTestExecutionLength",
            Type="String",
            Value=Ref(self.TestExecutionLengthSSMParameterValue),
        ))

        self.JMXFileNameSSMParameter = self.template.add_resource(SSMParameter(
            "JMXFileNameSSMParameter",
            Description="The Name of the JMX File",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterJMXFileName",
            Type="String",
            Value=Ref(self.JMXFileNameSSMParameterValue),
        ))

        self.S3JMXFileLocationSSMParameter = self.template.add_resource(SSMParameter(
            "S3JMXFileLocationSSMParameter",
            Description="Location of the JMX File in S3",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterS3JMXFileLocation",
            Type="String",
            Value=Ref(self.S3JMXFileLocationSSMParameterValue),
        ))

        self.JMXResultsFileNameSSMParameter = self.template.add_resource(SSMParameter(
            "JMXResultsFileNameSSMParameter",
            Description="The Name of The JMX Results File",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-JMeterJMXResultsFileName",
            Type="String",
            Value=Ref(self.JMXResultsFileNameSSMParameterValue),
        ))


    def add_outputs(self):
        self.template.add_output(Output(
            "JmeterMasterPublicLoadBalancerDnsName",
            Value=GetAtt(self.MasterPublicLoadBalancer, "DNSName"),
        ))

        self.template.add_output(Output(
            "TestExecutionLengthSSMParameterOutput",
            Value=Ref(self.TestExecutionLengthSSMParameter),
        ))

        self.template.add_output(Output(
            "JMXFileNameSSMParameterOutput",
            Value=Ref(self.JMXFileNameSSMParameter),
        ))

        self.template.add_output(Output(
            "S3JMXFileLocationSSMParameterOutput",
            Value=Ref(self.S3JMXFileLocationSSMParameter),
        ))

        self.template.add_output(Output(
            "JMXResultsFileNameSSMParameterOutput",
            Value=Ref(self.JMXResultsFileNameSSMParameter),
        ))


def sceptre_handler(sceptre_user_data):
    jmeter = JMeter(sceptre_user_data)
    return jmeter.template.to_json()
