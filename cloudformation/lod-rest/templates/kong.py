from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, GetAZs
from troposphere import elasticloadbalancing as elb, GetAZs
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
from troposphere.autoscaling import Tag as AutoScalingTag
from troposphere.ssm import Parameter as SSMParameter
import troposphere.elasticloadbalancingv2 as elb
from troposphere.elasticloadbalancingv2 import Certificate
from troposphere.iam import Role, InstanceProfile, Policy
from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole
import troposphere.iam as iam
from troposphere import FindInMap

class Kong(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()

        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
    
        #VPC Stack Output
        self.VpcId = self.template.add_parameter(Parameter(
            "VpcId",
            Type="String",
        ))

        #VPC Stack Output
        self.KongProxyAccess = self.template.add_parameter(Parameter(
            "KongProxyAccess",
            Type="String",
            Description="The IP Address range that can be used to access the Kong proxy port 8000",
        ))

        #VPC Stack Output
        self.KongAdminAccess = self.template.add_parameter(Parameter(
            "KongAdminAccess",
            Type="String",
            Description="The IP Address range that can be used to access the Kong Admin port 8001",
        ))

        # AdminCidrBlock is VPC Output
        self.AdminCidrBlock = self.template.add_parameter(Parameter(
            "AdminCidrBlock",
            Type="String",
        ))

        self.RESTPubSubnet1 = self.template.add_parameter(Parameter(
            "RESTPubSubnet1",
            Type="String",
        ))

        self.RESTPubSubnet2 = self.template.add_parameter(Parameter(
            "RESTPubSubnet2",
            Type="String",
        ))

        self.RESTPrivSubnet1 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet1",
            Type="String",
        ))

        self.RESTPrivSubnet2 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet2",
            Type="String",
        ))
        
        self.KongSSLCertificate = self.template.add_parameter(Parameter(
            "KongSSLCertificate",
            Type="String",
        ))

        self.CassandraSG = self.template.add_parameter(Parameter(
            "CassandraSG",
            Type="String",
        ))

        self.CassandraPort = self.template.add_parameter(Parameter(
            "CassandraPort",
            Type="String",
        ))

        self.KongInstanceType = self.template.add_parameter(Parameter(
            "KongInstanceType",
            Type="String",
        ))

        self.KongKeyName = self.template.add_parameter(Parameter(
            "KongKeyName",
            Type="String",
        ))

        self.KongIAMInstanceProfile = self.template.add_parameter(Parameter(
            "KongIAMInstanceProfile",
            Type="String",
        ))

        self.KongVersionSSMParameterValue = self.template.add_parameter(Parameter(
            "KongVersionSSMParameterValue",
            Type="String",
        ))

        self.KongExecuteMigrationsSSMParameterValue = self.template.add_parameter(Parameter(
            "KongExecuteMigrationsSSMParameterValue",
            Type="String",
        ))

        self.CassandraSeedListSSMParameterValue = self.template.add_parameter(Parameter(
            "CassandraSeedListSSMParameterValue",
            Type="String",
        ))

        self.OAuthRestApiProvisionKeySSMParameterValue = self.template.add_parameter(Parameter(
            "OAuthRestApiProvisionKeySSMParameterValue",
            Type="String",
        ))

        self.OAuthRestApiKongConsumerClientId = self.template.add_parameter(Parameter(
            "OAuthRestApiKongConsumerClientId",
            Type="String",
        ))

        self.OAuthRestApiKongConsumerClientSecret = self.template.add_parameter(Parameter(
            "OAuthRestApiKongConsumerClientSecret",
            Type="String",
        ))


    def add_resources(self):

        self.KongPublicLoadBalancerSecurityGroup = self.template.add_resource(ec2.SecurityGroup(
            "KongPublicLoadBalancerSecurityGroup",
            GroupDescription="Enable HTTP access on port 8000m and 8001 for Admin",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8443,
                    ToPort=8443,
                    CidrIp=Ref(self.KongProxyAccess),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8000,
                    ToPort=8000,
                    CidrIp=Ref(self.KongProxyAccess),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8444,
                    ToPort=8444,
                    CidrIp=Ref(self.KongAdminAccess),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    CidrIp=Ref(self.KongAdminAccess),
                )],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPublicLBSG"),
            ))

        self.KongPrivateLoadBalancerSecurityGroup = self.template.add_resource(ec2.SecurityGroup(
            "KongPrivateLoadBalancerSecurityGroup",
            GroupDescription="Enable HTTP access on port 8000 and 8001",
            VpcId=Ref(self.VpcId),
             SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8443,
                    ToPort=8443,
                    CidrIp=Ref(self.KongProxyAccess),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8000,
                    ToPort=8000,
                    CidrIp=Ref(self.KongProxyAccess),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8444,
                    ToPort=8444,
                    CidrIp=Ref(self.KongAdminAccess),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    CidrIp=Ref(self.KongAdminAccess),
                )],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPrivateLBSG"),
            ))

        self.KongPublicLoadBalancer = self.template.add_resource(elb.LoadBalancer(
            "KongPublicLoadBalancer",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPubLB",
            Scheme="internet-facing",
            Subnets=[Ref(self.RESTPubSubnet1), Ref(self.RESTPubSubnet2)],
            SecurityGroups=[Ref(self.KongPublicLoadBalancerSecurityGroup)],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPubLB"),
        ))

        self.KongPublicSecureProxyTargetGroup = self.template.add_resource(elb.TargetGroup(
            "KongPublicSecureProxyTargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTP",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(
                HttpCode="200"),
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPubSecProxyTG",
            Port="8443",
            Protocol="HTTPS",
            UnhealthyThresholdCount="3",
            VpcId=Ref(self.VpcId),
        ))

        self.KongPublicSecureAdminTargetGroup = self.template.add_resource(elb.TargetGroup(
            "KongPublicSecureAdminTargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTPS",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(
                HttpCode="200"),
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPubSecAdminTG",
            Port="8444",
            Protocol="HTTPS",
            UnhealthyThresholdCount="3",
            VpcId=Ref(self.VpcId),
        ))

        self.KongPrivateSecureProxyTargetGroup = self.template.add_resource(elb.TargetGroup(
            "KongPrivateSecureProxyTargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTPS",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(
                HttpCode="200"),
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPrivateSecProxyTG",
            Port="8443",
            Protocol="HTTPS",
            UnhealthyThresholdCount="3",
            VpcId=Ref(self.VpcId),
        ))

        self.KongPrivateSecureAdminTargetGroup = self.template.add_resource(elb.TargetGroup(
            "KongPrivateSecureAdminTargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTPS",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(
                HttpCode="200"),
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPrivSecAdminTG",
            Port="8444",
            Protocol="HTTPS",
            UnhealthyThresholdCount="3",
            VpcId=Ref(self.VpcId),
        ))

        self.KongPublicNonSecureAdminTargetGroup = self.template.add_resource(elb.TargetGroup(
            "KongPublicNonSecureAdminTargetGroup",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTP",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=elb.Matcher(
                HttpCode="200"),
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPubNonSecAdminTG",
            Port="8001",
            Protocol="HTTP",
            UnhealthyThresholdCount="3",
            VpcId=Ref(self.VpcId),
        ))

        self.KongPrivateLoadBalancer = self.template.add_resource(elb.LoadBalancer(
            "KongPrivateLoadBalancer",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPrivLB",
            Scheme="internal",
            Subnets=[Ref(self.RESTPrivSubnet1), Ref(self.RESTPrivSubnet2)],
            SecurityGroups=[Ref(self.KongPrivateLoadBalancerSecurityGroup)],
            Tags=Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongPrivLB") + self.base_tags,
        ))


        self.KongPublicSecureProxyListener = self.template.add_resource(elb.Listener(
            "KongPublicSecureProxyListener",
            Port="8443",
            Protocol="HTTPS",
            SslPolicy="ELBSecurityPolicy-2016-08",
            LoadBalancerArn=Ref(self.KongPublicLoadBalancer),
            Certificates=[Certificate(
                            CertificateArn=Ref(self.KongSSLCertificate)
                            )],
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.KongPublicSecureProxyTargetGroup)
            )]
        ))

        self.KongPublicSecureAdminListener = self.template.add_resource(elb.Listener(
            "KongPublicSecureAdminListener",
            Port="8444",
            Protocol="HTTPS",
            SslPolicy="ELBSecurityPolicy-2016-08",
            LoadBalancerArn=Ref(self.KongPublicLoadBalancer),
            Certificates=[Certificate(
                            CertificateArn=Ref(self.KongSSLCertificate))],
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.KongPublicSecureAdminTargetGroup)
            )]
            
        ))

        self.KongPrivateSecureProxyListener = self.template.add_resource(elb.Listener(
            "KongPrivateSecureProxyListener",
            Port="8443",
            Protocol="HTTPS",
            SslPolicy="ELBSecurityPolicy-2016-08",
            LoadBalancerArn=Ref(self.KongPrivateLoadBalancer),
            Certificates=[Certificate(
                            CertificateArn=Ref(self.KongSSLCertificate))],
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.KongPrivateSecureProxyTargetGroup)

            )]
        ))

        self.KongPrivateSecureAdminListener = self.template.add_resource(elb.Listener(
            "KongPrivateSecureAdminListener",
            Port="8444",
            Protocol="HTTPS",
            SslPolicy="ELBSecurityPolicy-2016-08",
            LoadBalancerArn=Ref(self.KongPrivateLoadBalancer),
            Certificates=[Certificate(
                            CertificateArn=Ref(self.KongSSLCertificate))],
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.KongPrivateSecureAdminTargetGroup)
            )]
        ))

        self.KongPublicNonSecureAdminListener = self.template.add_resource(elb.Listener(
            "KongPublicNonSecureAdminListener",
            Port="8001",
            Protocol="HTTP",
            LoadBalancerArn=Ref(self.KongPublicLoadBalancer),
            DefaultActions=[elb.Action(
                Type="forward",
                TargetGroupArn=Ref(self.KongPublicNonSecureAdminTargetGroup)

            )]
        ))

        self.KongEC2SecurityGroup = self.template.add_resource(ec2.SecurityGroup(
            "KongEC2SecurityGroup",
            GroupDescription="Enable SSH access and HTTP access on the inbound Port",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8000,
                    ToPort=8001,
                    SourceSecurityGroupId=Ref(self.KongPublicLoadBalancerSecurityGroup),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8443,
                    ToPort=8444,
                    SourceSecurityGroupId=Ref(self.KongPublicLoadBalancerSecurityGroup),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8000,
                    ToPort=8001,
                    SourceSecurityGroupId=Ref(self.KongPrivateLoadBalancerSecurityGroup),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8443,
                    ToPort=8444,
                    SourceSecurityGroupId=Ref(self.KongPrivateLoadBalancerSecurityGroup),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=8443,
                    ToPort=8444,
                    SourceSecurityGroupId=Ref(self.KongPrivateLoadBalancerSecurityGroup),
                )],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongEc2SG"),
        ))

        self.CassandraSGKongCommunicationIngress = self.template.add_resource(ec2.SecurityGroupIngress(
            "CassandraSGKongCommunicationIngress",
            DependsOn=self.KongEC2SecurityGroup,
            GroupId=Ref(self.CassandraSG),
            IpProtocol="tcp",
            FromPort=Ref(self.CassandraPort),
            ToPort=Ref(self.CassandraPort),
            SourceSecurityGroupId=Ref(self.KongEC2SecurityGroup),
        ))

        self.ASGUpdateRole = self.template.add_resource(Role(
            "ASGUpdateRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["ec2.amazonaws.com"])
                        )
                    ]
                ),
            Policies=[iam.Policy(
                PolicyName="ASGUpdateRole",
                PolicyDocument={"Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Action": [
                                            "ec2:Describe*",
                                            "cloudformation:DescribeStackResource"
                                        ],
                                        "Effect": "Allow",
                                        "Resource": "*"
                                      }]}
                                )
                            ]
        ))

        self.ASGUpdateProfile = self.template.add_resource(InstanceProfile(
            "ASGUpdateProfile",
            Path="/",
            Roles=[Ref(self.ASGUpdateRole)],
        ))

        self.KongVersionSSMParameter = self.template.add_resource(SSMParameter(
            "KongVersionSSMParameter",
            Description="The Kong Version",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongVersion",
            Type="String",
            Value=Ref(self.KongVersionSSMParameterValue),
        ))

        self.KongExecuteMigrationsSSMParameter = self.template.add_resource(SSMParameter(
            "KongExecuteMigrationsSSMParameter",
            Description="Flag to determine if Kong should Execute DB migrations",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-KongExecuteMigrations",
            Type="String",
            Value=Ref(self.KongExecuteMigrationsSSMParameterValue),
        ))

        self.CassandraSeedListSSMParameter = self.template.add_resource(SSMParameter(
            "CassandraSeedListSSMParameter",
            Description="The Cassandra Seed Node List",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraSeedList",
            Type="String",
            Value=Ref(self.CassandraSeedListSSMParameterValue),
        ))

        self.KongLaunchConfig = self.template.add_resource(LaunchConfiguration(
            "KongLaunchConfig",
            ImageId="ami-a4c7edb2",
            AssociatePublicIpAddress="false",
            InstanceType=Ref(self.KongInstanceType),
            IamInstanceProfile=Ref(self.KongIAMInstanceProfile),
            KeyName=Ref(self.KongKeyName),
            SecurityGroups=[Ref(self.KongEC2SecurityGroup)],
            UserData=Base64(Join('', [
            "#!/bin/bash\n",
            "yum update -y \n",
            "pip install --upgrade pip \n",
            "pip install --upgrade awscli \n",
            "ClientCode=\"" + self.environment_parameters["ClientEnvironmentKey"] + "\" \n",
            "REGION=\"" + self.environment_parameters["EnvironmentRegion"] + "\" \n",
            "BootstrapRepositorySSMKey=\"-bootstrapRepository\" \n",
            "BootstrapRepositorySSMKey=${ClientCode}${BootstrapRepositorySSMKey} \n",
            "echo $BootstrapRepositorySSMKey \n",
            "bootstrapRepository=\"$(aws ssm get-parameter --name ${BootstrapRepositorySSMKey} --region ${REGION} --output text --query 'Parameter.Value')\" \n",
            "echo $bootstrapRepository \n",
            "keyprefix=\"/bootstrap/rest/bash\" \n",
            "localpath=\"/tmp/bootstrap\" \n",
            "echo $bootStrapRepository \n",
            "if [ ! -d \"${localpath}\"]; then \n",
            "mkdir - p \n",
            "\"${localpath}\" \n",
            "fi \n",
            "FullS3Path=${bootstrapRepository}${keyprefix} \n",
            "echo $FullS3Path \n",
            "aws s3 sync s3://$FullS3Path $localpath \n",
            "chmod u+x /tmp/bootstrap/kong-provision.sh \n",
            "/bin/bash /tmp/bootstrap/kong-provision.sh \n",]))
         ))

        self.KongScalingGroup = self.template.add_resource(AutoScalingGroup(
            "KongScalingGroup",
            AutoScalingGroupName=self.environment_parameters["ClientEnvironmentKey"] + "-KongAutoScalingGroup",
            AvailabilityZones=["us-east-1a"],
            LaunchConfigurationName=Ref(self.KongLaunchConfig),
            VPCZoneIdentifier=[Ref(self.RESTPrivSubnet1)],
            MinSize="1",
            MaxSize="1",
            DesiredCapacity="1",
            TargetGroupARNs=[Ref(self.KongPublicNonSecureAdminTargetGroup), Ref(self.KongPrivateSecureAdminTargetGroup),
                            Ref(self.KongPrivateSecureProxyTargetGroup), Ref(self.KongPublicSecureAdminTargetGroup),
                            Ref(self.KongPublicSecureProxyTargetGroup)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-Kong-Ec2", True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientEnvironmentKey"], True),
            ],
         ))


    def add_outputs(self):
        self.template.add_output(Output(
            "KongPrivateLoadBalancerSecurityGroup",
            Value=Ref(self.KongPrivateLoadBalancerSecurityGroup),
        ))

        self.template.add_output(Output(
            "KongPrivateInternalLoadBalancerDNS",
            Value=GetAtt(self.KongPrivateLoadBalancer, "DNSName"),
        ))

        self.template.add_output(Output(
            "KongPublicLoadBalancerSecurityGroup",
            Value=Ref(self.KongPublicLoadBalancerSecurityGroup),
        ))

        self.template.add_output(Output(
            "KongPublicLoadBalancerDNS",
            Value=GetAtt(self.KongPublicLoadBalancer, "DNSName"),
        ))

        self.template.add_output(Output(
            "OAuthRestApiProvisionKeySSMParameterValue",
            Value=Ref(self.OAuthRestApiProvisionKeySSMParameterValue),
        ))

        self.template.add_output(Output(
            "OAuthRestApiKongConsumerClientId",
            Value=Ref(self.OAuthRestApiKongConsumerClientId),
        ))

        self.template.add_output(Output(
            "OAuthRestApiKongConsumerClientSecret",
            Value=Ref(self.OAuthRestApiKongConsumerClientSecret),
        ))

        
def sceptre_handler(sceptre_user_data):
    kong = Kong(sceptre_user_data)
    return kong.template.to_json()
