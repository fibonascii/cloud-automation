from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, elasticloadbalancing
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, LifecycleHookSpecification
from troposphere.autoscaling import Tag as AutoScalingTag
from troposphere.iam import Role, InstanceProfile, Policy
from awacs.aws import Allow, Statement, Principal, Policy
from awacs.sts import AssumeRole
from troposphere import eks
import troposphere.iam as iam

class SharedServicesEks(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()

        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
        # SharedServicesVpcId is VPC Output
        self.SharedServicesVpcId = self.template.add_parameter(Parameter(
            "SharedServicesVpcId",
            Type="String",
        ))

        # SharedServicesPrivSubnet1 is VPC Output
        self.SharedServicesPrivSubnet1 = self.template.add_parameter(Parameter(
            "SharedServicesPrivSubnet1",
            Type="String",
        ))

        # SharedServicesPrivSubnet2 is VPC Output
        self.SharedServicesPrivSubnet2 = self.template.add_parameter(Parameter(
            "SharedServicesPrivSubnet2",
            Type="String",
        ))

        # SharedServicesPubSubnet1 is VPC Output
        self.SharedServicesPubSubnet1 = self.template.add_parameter(Parameter(
            "SharedServicesPubSubnet1",
            Type="String",
        ))

        # SharedServicesPubSubnet2 is VPC Output
        self.SharedServicesPubSubnet2 = self.template.add_parameter(Parameter(
            "SharedServicesPubSubnet2",
            Type="String",
        ))

        self.EksClusterVersion = self.template.add_parameter(Parameter(
            "EksClusterVersion",
            Type="String",
        ))

        self.WorkerNodeImageId = self.template.add_parameter(Parameter(
            "WorkerNodeImageId",
            Type="String",
        ))

        self.WorkerNodeKeyName = self.template.add_parameter(Parameter(
            "WorkerNodeKeyName",
            Type="String",
        ))

        self.WorkerNodeInstanceType = self.template.add_parameter(Parameter(
            "WorkerNodeInstanceType",
            Type="String",
        ))

        self.WorkerNodeASGGroupMinSize = self.template.add_parameter(Parameter(
            "WorkerNodeASGGroupMinSize",
            Type="String",
        ))

        self.WorkerNodeASGGroupDesiredSize = self.template.add_parameter(Parameter(
            "WorkerNodeASGGroupDesiredSize",
            Type="String",
        ))

        self.WorkerNodeASGGroupMaxSize = self.template.add_parameter(Parameter(
            "WorkerNodeASGGroupMaxSize",
            Type="String",
        ))

        self.WorkerNodeASGHealthCheckType = self.template.add_parameter(Parameter(
            "WorkerNodeASGHealthCheckType",
            Type="String",
        ))

        self.WorkerNodeASGHealthCheckGracePeriod = self.template.add_parameter(Parameter(
            "WorkerNodeASGHealthCheckGracePeriod",
            Type="String",
        ))

        self.WorkerNodeASGCoolDown = self.template.add_parameter(Parameter(
            "WorkerNodeASGCoolDown",
            Type="String",
        ))

    def add_resources(self):
        self.EKSControlPlaneSG = self.template.add_resource(ec2.SecurityGroup(
            "EKSControlPlaneSG",
            GroupDescription="Allow communication between WorkerNodes and EKS",
            VpcId=Ref(self.SharedServicesVpcId),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-EksControlPlane-SG"),
        ))

        self.EKSClusterRole = self.template.add_resource(Role(
            "EKSClusterRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["eks.amazonaws.com"])
                    )
                ]
            ),
            ManagedPolicyArns=["arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
                               "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"],
        ))

        self.EKSCluster = self.template.add_resource(eks.Cluster(
            "EKSCluster",
            DependsOn=["EKSControlPlaneSG", "EKSClusterRole"],
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-EKS",
            RoleArn=GetAtt(self.EKSClusterRole, "Arn"),
            Version=Ref(self.EksClusterVersion),
            ResourcesVpcConfig=eks.ResourcesVpcConfig(
                SecurityGroupIds=[Ref(self.EKSControlPlaneSG)],
                SubnetIds=[Ref(self.SharedServicesPubSubnet1), Ref(self.SharedServicesPubSubnet2)],
            ),

        ))


        self.WorkerNodeEc2SG = self.template.add_resource(ec2.SecurityGroup(
            "WorkerNodeEc2SG",
            DependsOn=["EKSCluster"],
            GroupDescription="Allow communication between WorkerNodes and EKS",
            VpcId=Ref(self.SharedServicesVpcId),
            Tags=self.base_tags +
                 Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-EksWorkerNodes-Ec2SG") +
                 Tags({"kubernetes.io/cluster/" + self.environment_parameters["ClientEnvironmentKey"] + "-SS-EKS": "owned"}),
        ))

        self.WorkerNodeInstanceRole = self.template.add_resource(Role(
            "WorkerNodeInstanceRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["ec2.amazonaws.com"])
                    )
                ]
            ),
            ManagedPolicyArns=["arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
                               "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
                               "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"],
        ))

        self.WorkerNodeInstanceProfile = self.template.add_resource(InstanceProfile(
            "WorkerNodeInstanceProfile",
            Path="/",
            Roles=[Ref(self.WorkerNodeInstanceRole)],
        ))

        self.WorkerNodeEc2SGIngress = self.template.add_resource(ec2.SecurityGroupIngress(
            "WorkerNodeEc2SGIngress",
            DependsOn=["WorkerNodeEc2SG"],
            GroupId=Ref(self.WorkerNodeEc2SG),
            IpProtocol="-1",
            FromPort=0,
            ToPort=65535,
            SourceSecurityGroupId=Ref(self.WorkerNodeEc2SG),
        ))

        self.WorkerNodeEc2SGIngressFromEKSControlPlane = self.template.add_resource(ec2.SecurityGroupIngress(
            "WorkerNodeEc2SGIngressFromEKSControlPlane",
            DependsOn=["WorkerNodeEc2SG"],
            GroupId=Ref(self.WorkerNodeEc2SG),
            IpProtocol="tcp",
            FromPort=1025,
            ToPort=65535,
            SourceSecurityGroupId=Ref(self.EKSControlPlaneSG),
        ))

        self.EksControlPlaneEgressToWorkerNodes = self.template.add_resource(ec2.SecurityGroupEgress(
            "EksControlPlaneEgressToWorkerNodes",
            DependsOn=["WorkerNodeEc2SG"],
            GroupId=Ref(self.EKSControlPlaneSG),
            IpProtocol="tcp",
            FromPort=1025,
            ToPort=65535,
            DestinationSecurityGroupId=Ref(self.WorkerNodeEc2SG),
        ))

        self.WorkerNodeEc2SG443IngressFromEKSControlPlane = self.template.add_resource(ec2.SecurityGroupIngress(
            "WorkerNodeEc2SG443IngressFromEKSControlPlane",
            DependsOn=["WorkerNodeEc2SG"],
            GroupId=Ref(self.WorkerNodeEc2SG),
            IpProtocol="tcp",
            FromPort=443,
            ToPort=443,
            SourceSecurityGroupId=Ref(self.EKSControlPlaneSG),
        ))

        self.EKSControlPlaneSG443IngressFromWorkerNode = self.template.add_resource(ec2.SecurityGroupIngress(
            "EKSControlPlaneSG443IngressFromWorkerNode",
            DependsOn=["WorkerNodeEc2SG"],
            GroupId=Ref(self.EKSControlPlaneSG),
            IpProtocol="tcp",
            FromPort=443,
            ToPort=443,
            SourceSecurityGroupId=Ref(self.WorkerNodeEc2SG),
        ))

        self.EksControlPlane443EgressToWorkerNodes = self.template.add_resource(ec2.SecurityGroupEgress(
            "EksControlPlane443EgressToWorkerNodes",
            DependsOn=["WorkerNodeEc2SG"],
            GroupId=Ref(self.EKSControlPlaneSG),
            IpProtocol="tcp",
            FromPort=443,
            ToPort=443,
            DestinationSecurityGroupId=Ref(self.WorkerNodeEc2SG),
        ))

        self.WorkerNodeLaunchConfiguration = self.template.add_resource(LaunchConfiguration(
            "WorkerNodeLaunchConfiguration",
            ImageId=Ref(self.WorkerNodeImageId),
            InstanceType=Ref(self.WorkerNodeInstanceType),
            IamInstanceProfile=Ref(self.WorkerNodeInstanceProfile),
            KeyName=Ref(self.WorkerNodeKeyName),
            SecurityGroups=[Ref(self.WorkerNodeEc2SG)],
            UserData=Base64(Join('', [
                "#!/bin/bash \n",
                "set -o xtrace \n"
                "ClusterName=\"" + self.environment_parameters["ClientEnvironmentKey"] + "-SS-EKS" + "\" \n",
                "BootstrapArguments=\"""\" \n",
                "/etc/eks/bootstrap.sh ${ClusterName} ${BootstrapArguments} \n"
                 ]))
        ))

        self.WorkerNodeAutoScalingGroup = self.template.add_resource(AutoScalingGroup(
            "WorkerNodeAutoscalingGroup",
            AutoScalingGroupName=self.environment_parameters["ClientEnvironmentKey"] + "-SS-EksWorkerNodeAutoScalingGroup",
            LaunchConfigurationName=Ref(self.WorkerNodeLaunchConfiguration),
            MaxSize=Ref(self.WorkerNodeASGGroupMaxSize),
            MinSize=Ref(self.WorkerNodeASGGroupMinSize),
            DesiredCapacity=Ref(self.WorkerNodeASGGroupDesiredSize),
            HealthCheckType=Ref(self.WorkerNodeASGHealthCheckType),
            HealthCheckGracePeriod=Ref(self.WorkerNodeASGHealthCheckGracePeriod),
            Cooldown=Ref(self.WorkerNodeASGCoolDown),
            VPCZoneIdentifier=[Ref(self.SharedServicesPrivSubnet1), Ref(self.SharedServicesPrivSubnet2)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-SS-EKS" + "-WorkerNodeGroup-Node", True),
                AutoScalingTag("kubernetes.io/cluster/" + self.environment_parameters["ClientEnvironmentKey"] + "-SS-EKS", "owned", True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientEnvironmentKey"], True),
            ],
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "WorkerNodeEc2SG",
            Value=Ref(self.WorkerNodeEc2SG),
        ))

        self.template.add_output(Output(
            "EKSClusterName",
            Value=Ref(self.EKSCluster),
        ))

        self.template.add_output(Output(
            "WorkerNodeInstanceRoleArn",
            Value=GetAtt(self.WorkerNodeInstanceRole, "Arn"),
        ))

        self.template.add_output(Output(
            "WorkerNodeAutoScalingGroupName",
            Value=Ref(self.WorkerNodeAutoScalingGroup),
        ))

def sceptre_handler(sceptre_user_data):
    sseks = SharedServicesEks(sceptre_user_data)
    return sseks.template.to_json()
