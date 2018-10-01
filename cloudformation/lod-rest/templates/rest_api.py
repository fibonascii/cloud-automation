from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, elasticloadbalancing
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, LifecycleHookSpecification
from troposphere.autoscaling import Tag as AutoScalingTag
from troposphere.ssm import Parameter as SSMParameter

class RestApi(BaseCloudFormation):
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

        # AdminCidrBlock is VPC Output
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

        # KongPrivateLoadBalancerSecurityGroup is a KONG Output
        self.KongPrivateLoadBalancerSecurityGroup = self.template.add_parameter(Parameter(
            "KongPrivateLoadBalancerSecurityGroup",
            Type="String",
        ))

        self.RestApiImageId = self.template.add_parameter(Parameter(
            "RestApiImageId",
            Type="String",
        ))

        self.RestApiKeyName = self.template.add_parameter(Parameter(
            "RestApiKeyName",
            Type="String",
        ))

        self.RestApiInstanceType = self.template.add_parameter(Parameter(
            "RestApiInstanceType",
            Type="String",
        ))

        self.RestApiIAMInstanceProfile = self.template.add_parameter(Parameter(
            "RestApiIAMInstanceProfile",
            Type="String",
        ))

        self.RestApiASGGroupMinSize = self.template.add_parameter(Parameter(
            "RestApiASGGroupMinSize",
            Type="String",
        ))

        self.RestApiASGGroupDesiredSize = self.template.add_parameter(Parameter(
            "RestApiASGGroupDesiredSize",
            Type="String",
        ))

        self.RestApiASGGroupMaxSize = self.template.add_parameter(Parameter(
            "RestApiASGGroupMaxSize",
            Type="String",
        ))

        self.RestApiASGHealthCheckType = self.template.add_parameter(Parameter(
            "RestApiASGHealthCheckType",
            Type="String",
        ))

        self.RestApiASGHealthCheckGracePeriod = self.template.add_parameter(Parameter(
            "RestApiASGHealthCheckGracePeriod",
            Type="String",
        ))

        self.RestApiASGCoolDown = self.template.add_parameter(Parameter(
            "RestApiASGCoolDown",
            Type="String",
        ))

        self.RestApiASGLifeCycleTransition = self.template.add_parameter(Parameter(
            "RestApiASGLifeCycleTransition",
            Type="String",
        ))

        self.RestApiASGLifeCycleHeartBeatTimeout = self.template.add_parameter(Parameter(
            "RestApiASGLifeCycleHeartBeatTimeout",
            Type="String",
        ))

    def add_resources(self):
        self.RestApiPublicLBSG = self.template.add_resource(ec2.SecurityGroup(
            "RestApiPublicLBSG",
            GroupDescription="Loadbalancer Security Group For Rest Api Public LB",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=3389,
                    ToPort=3389,
                    CidrIp=Ref(self.AdminCidrBlock),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiPubLBSG"),
            ))

        self.RestApiPrivateLBSG = self.template.add_resource(ec2.SecurityGroup(
            "RestApiPrivateLBSG",
            GroupDescription="Loadbalancer Security Group For Rest Api Private LB",
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
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiPrivLBSG"),
            ))

        self.RestApiSG = self.template.add_resource(ec2.SecurityGroup(
            "RestApiSG",
            GroupDescription="Allow communication between Rest Api Load Balancers and Rest Api Ec2s",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=3389,
                    ToPort=3389,
                    SourceSecurityGroupId=Ref(self.RestApiPublicLBSG),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    SourceSecurityGroupId=Ref(self.RestApiPublicLBSG),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=80,
                    ToPort=80,
                    SourceSecurityGroupId=Ref(self.RestApiPrivateLBSG),
                ),
            ],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiEc2SG"),
            ))

        self.ApiEc2ToKongPrivateALBIngress = self.template.add_resource(ec2.SecurityGroupIngress(
            "ApiEc2ToKongPrivateALBIngress",
            DependsOn=self.RestApiSG,
            GroupId=Ref(self.KongPrivateLoadBalancerSecurityGroup),
            IpProtocol="tcp",
            FromPort=8443,
            ToPort=8444,
            SourceSecurityGroupId=Ref(self.RestApiSG),
        ))

        self.RestApiPublicLoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "RestApiPublicLoadBalancer",
            LoadBalancerName=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiPubLB",
            Scheme="internet-facing",
            Listeners=[
                elasticloadbalancing.Listener(
                    LoadBalancerPort="3389",
                    InstancePort="3389",
                    Protocol="TCP",
                    InstanceProtocol="TCP",
                )
            ],
            Instances=[],
            SecurityGroups=[Ref(self.RestApiPublicLBSG)],
            Subnets=[Ref(self.RESTPubSubnet1),Ref(self.RESTPubSubnet2)],
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
                Timeout="5",),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiPubLB"),
            ))

        self.RestApiPrivateLoadBalancer = self.template.add_resource(elasticloadbalancing.LoadBalancer(
            "RestApiPrivateLoadBalancer",
            LoadBalancerName=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiPrivLB",
            Scheme="internal",
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
                    Protocol="TCP",
                    InstanceProtocol="TCP",
                )
            ],
            Instances=[],
            SecurityGroups=[Ref(self.RestApiPrivateLBSG)],
            Subnets=[Ref(self.RESTPrivSubnet1), Ref(self.RESTPrivSubnet2)],
            ConnectionDrainingPolicy=elasticloadbalancing.ConnectionDrainingPolicy(
                Enabled=True,
                Timeout=120,
            ),
            CrossZone=True,
            HealthCheck=elasticloadbalancing.HealthCheck(
                Target=Join("", ["HTTP:", "80", "/swagger/index.html"]),
                HealthyThreshold="3",
                UnhealthyThreshold="5",
                Interval="30",
                Timeout="5",),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiPrivLB"),
            ))

        self.RestApiLaunchConfiguration = self.template.add_resource(LaunchConfiguration(
            "RestApiLaunchConfiguration",
            ImageId=Ref(self.RestApiImageId),
            InstanceType=Ref(self.RestApiInstanceType),
            IamInstanceProfile=Ref(self.RestApiIAMInstanceProfile),
            KeyName=Ref(self.RestApiKeyName),
            SecurityGroups=[Ref(self.RestApiSG)],
            UserData=Base64(Join('', [
            "<persist>true</persist>\n",
            "<powershell>\n",
            "$ClientCode = '" + self.environment_parameters["ClientEnvironmentKey"] + "'\n",
            "$bootstrapRepository = (Get-SSMParameterValue -Names $ClientCode-bootstrapRepository -WithDecryption $true).Parameters[0].Value\n",
            "\n",
            "$region = '" + self.environment_parameters["EnvironmentRegion"] + "'\n",
            "$keyPrefix = 'bootstrap/rest/powershell/'\n",
            "\n",
            "$localPath = 'C:/bootstrap/rest/powershell'\n",
            "\n",
            "if (-Not (Test-Path -Path $localPath)){New-Item -Path $localPath -ItemType directory -Force | out-null}\n",
            "$artifacts = Get-S3Object -BucketName $bootstrapRepository -KeyPrefix $keyPrefix -Region $region\n",
            "foreach($artifact in $artifacts) {$localFileName = $artifact.Key -replace $keyPrefix, '' \n",
            "if ($localFileName -ne '') {$localFilePath = Join-Path $localPath $localFileName \n",
            "Copy-S3Object -BucketName $bootstrapRepository -Key $artifact.Key -LocalFile $localFilePath -Region $region}} \n",
            "\n",
            "$cmdExecuteBootStrapping = 'C:\\bootstrap\\rest\\powershell\\ExecuteScripts.ps1' \n",
            "Invoke-Expression \"$cmdExecuteBootStrapping\" \n",
            "</powershell>", "\n"
            ]))
        ))

        self.RestApiAutoScalingGroup = self.template.add_resource(AutoScalingGroup(
            "RestApiAutoscalingGroup",
            AutoScalingGroupName=self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApiAutoScalingGroup",
            LaunchConfigurationName=Ref(self.RestApiLaunchConfiguration),
            LoadBalancerNames=[Ref(self.RestApiPublicLoadBalancer),Ref(self.RestApiPrivateLoadBalancer)],
            MaxSize=Ref(self.RestApiASGGroupMaxSize),
            MinSize=Ref(self.RestApiASGGroupMinSize),
            DesiredCapacity=Ref(self.RestApiASGGroupDesiredSize),
            HealthCheckType=Ref(self.RestApiASGHealthCheckType),
            HealthCheckGracePeriod=Ref(self.RestApiASGHealthCheckGracePeriod),
            Cooldown=Ref(self.RestApiASGCoolDown),
            LifecycleHookSpecificationList=[
                LifecycleHookSpecification(
                    HeartbeatTimeout=Ref(self.RestApiASGLifeCycleHeartBeatTimeout),
                    LifecycleTransition=Ref(self.RestApiASGLifeCycleTransition),
                    LifecycleHookName=self.environment_parameters["ClientEnvironmentKey"] + "-REST-API-LCH"),
                ],
            VPCZoneIdentifier=[Ref(self.RESTPrivSubnet1),Ref(self.RESTPrivSubnet2)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-LoyaltyRestApi-Ec2", True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientEnvironmentKey"], True),
            ],
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "ApiServerEC2SecurityGroup",
            Value=Ref(self.RestApiSG),
        ))

        self.template.add_output(Output(
            "RestApiPublicLoadBalancer",
            Value=GetAtt(self.RestApiPublicLoadBalancer, "DNSName"),
        ))

        self.template.add_output(Output(
            "RestApiPrivateLoadBalancerDNS",
            Value=GetAtt(self.RestApiPrivateLoadBalancer, "DNSName"),
        ))

        self.template.add_output(Output(
            "RestApiAutoScalingGroup",
            Value=Ref(self.RestApiAutoScalingGroup),
        ))

def sceptre_handler(sceptre_user_data):
    restapi = RestApi(sceptre_user_data)
    return restapi.template.to_json()
