from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output
from troposphere.s3 import Bucket, s3_bucket_name, VersioningConfiguration
from troposphere.ssm import Parameter as SSMParameter

class VPC(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()

        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):

        self.AdminCidrBlock = self.template.add_parameter(Parameter(
            "AdminCidrBlock",
            Type="String",
            Description="The Admin Cidr Block",
        ))

        self.VpcCidr = self.template.add_parameter(Parameter(
            "VpcCidr",
            Type="String",
        ))

        self.RESTPubSub1Cidr = self.template.add_parameter(Parameter(
            "RESTPubSub1Cidr",
            Type="String",
        ))

        self.RESTPubSub2Cidr = self.template.add_parameter(Parameter(
            "RESTPubSub2Cidr",
            Type="String",
        ))

        self.RESTPrivSub1Cidr = self.template.add_parameter(Parameter(
            "RESTPrivSub1Cidr",
            Type="String",
        ))

        self.RESTPrivSub2Cidr = self.template.add_parameter(Parameter(
            "RESTPrivSub2Cidr",
            Type="String",
        ))

        self.BootstrapRepositorySSMParameterValue = self.template.add_parameter(Parameter(
            "BootstrapRepositorySSMParameterValue",
            Type="String",
        ))



    def add_resources(self):
        """ Add All Cloudformation Resources. This will include vpc, igw, and any other network
        resources """
        self.vpc = self.template.add_resource(ec2.VPC(
             "VPC",
             CidrBlock=Ref(self.VpcCidr),
             EnableDnsSupport=True,
             Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-VPC"),
        ))

        self.RESTPubSubnet1 = self.template.add_resource(ec2.Subnet(
            "RESTPubSubnet1",
            CidrBlock=Ref(self.RESTPubSub1Cidr),
            VpcId=Ref(self.vpc),
            AvailabilityZone="us-east-1a",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPubSubnet1"),
       ))

        self.RESTPubSubnet2 = self.template.add_resource(ec2.Subnet(
            "RESTPubSubnet2",
            VpcId=Ref(self.vpc),
            CidrBlock=Ref(self.RESTPubSub2Cidr),
            AvailabilityZone="us-east-1b",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPubSubnet2"),
        ))

        self.RESTPrivSubnet1 = self.template.add_resource(ec2.Subnet(
            "RESTPrivSubnet1",
            VpcId=Ref(self.vpc),
            CidrBlock=Ref(self.RESTPrivSub1Cidr),
            AvailabilityZone="us-east-1a",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPrivSubnet1"),
        ))

        self.RESTPrivSubnet2 = self.template.add_resource(ec2.Subnet(
            "RESTPrivSubnet2",
            CidrBlock=Ref(self.RESTPrivSub2Cidr),
            VpcId=Ref(self.vpc),
            AvailabilityZone="us-east-1b",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPrivSubnet2"),
        ))

        self.RESTIGW = self.template.add_resource(ec2.InternetGateway(
            "RESTIGW",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTIGW"),
        ))

        self.RESTIGWAttachment = self.template.add_resource(ec2.VPCGatewayAttachment(
            "IGWAttachment",
            VpcId=Ref(self.vpc),
            InternetGatewayId=Ref(self.RESTIGW),
        ))

        self.RESTEIP1 = self.template.add_resource(ec2.EIP(
            "RESTEIP1",
            Domain="vpc",
        ))

        self.RESTEIP2 = self.template.add_resource(ec2.EIP(
            "RESTEIP2",
            Domain="vpc",
        ))

        self.RESTNAT1 = self.template.add_resource(ec2.NatGateway(
            "NAT",
            AllocationId=GetAtt(self.RESTEIP1, "AllocationId"),
            SubnetId=Ref(self.RESTPubSubnet1),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTNAT1"),
        ))
        
        self.RESTNAT2 = self.template.add_resource(ec2.NatGateway(
            "NAT2",
            AllocationId=GetAtt(self.RESTEIP2, "AllocationId"),
            SubnetId=Ref(self.RESTPubSubnet2),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTNAT2"),
        ))

        self.RESTPrivRT1 = self.template.add_resource(ec2.RouteTable(
            "RESTPrivRT1",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPRIVRT1"),
        ))

        self.RESTPrivRT2 = self.template.add_resource(ec2.RouteTable(
            "RESTPrivRT2",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPRIVRT2"),
        ))

        self.RESTNatRoute = self.template.add_resource(ec2.Route(
            "RESTNatRoute",
            RouteTableId=Ref(self.RESTPrivRT1),
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId=Ref(self.RESTNAT1),
        ))

        self.RESTNat2Route = self.template.add_resource(ec2.Route(
            "RESTNatRoute2",
            RouteTableId=Ref(self.RESTPrivRT2),
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId=Ref(self.RESTNAT2),
        ))

        self.RESTPrivRT1Association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "RESTPrivRT1Association",
            SubnetId=Ref(self.RESTPrivSubnet1),
            RouteTableId=Ref(self.RESTPrivRT1),
        ))

        self.RESTPrivRT2Association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "RESTPrivRT2Association",
            SubnetId=Ref(self.RESTPrivSubnet2),
            RouteTableId=Ref(self.RESTPrivRT2),
        ))

        self.RESTPubRT1 = self.template.add_resource(ec2.RouteTable(
            "RESTPubRT1",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPUBRT1"),
        ))

        self.RESTPubRT2 = self.template.add_resource(ec2.RouteTable(
            "RESTPubRT2",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-RESTPUBRT2"),
        ))

        self.RESTPubRT1IGWattachment = self.template.add_resource(ec2.Route(
            "RESTPubRT1IGWAttachment",
            RouteTableId=Ref(self.RESTPubRT1),
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=Ref(self.RESTIGW),
        ))

        self.RESTPubRT2IGWattachment = self.template.add_resource(ec2.Route(
            "RESTPubRT2IGWAttachment",
            RouteTableId=Ref(self.RESTPubRT2),
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=Ref(self.RESTIGW),
        ))

        self.RESTPubRT1Association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "RESTPubRT1Associate",
            SubnetId=Ref(self.RESTPubSubnet1),
            RouteTableId=Ref(self.RESTPubRT1),
        ))

        self.RESTPubRT2Asocation = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "RESTPubR2Associate",
            SubnetId=Ref(self.RESTPubSubnet2),
            RouteTableId=Ref(self.RESTPubRT2),
        ))

        self.EnvironmentArtifactsBucket = self.template.add_resource(Bucket(
            "EnvironmentArtifactsBucket",
            BucketName=(self.environment_parameters["ClientEnvironmentKey"] + "-environment-artifacts").lower(),
            AccessControl="BucketOwnerRead",
            VersioningConfiguration=VersioningConfiguration(
                Status="Enabled",
            ),
        ))

        self.BootstrapRepositorySSMParameter = self.template.add_resource(SSMParameter(
            "BootstrapRepositorySSMParameter",
            Description="The Bootstrap Repository",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-bootstrapRepository",
            Type="String",
            Value=Ref(self.BootstrapRepositorySSMParameterValue),
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "VpcId",
            Description="VpcId Output",
            Value=Ref(self.vpc)
        ))

        self.template.add_output(Output(
            "RESTPubSubnet1",
            Description="Loyalty On Demand Rest Public Subnet 1",
            Value=Ref(self.RESTPubSubnet1)
        ))

        self.template.add_output(Output(
            "RESTPubSubnet2",
            Description="Loyalty On Demand Rest Public Subnet 2",
            Value=Ref(self.RESTPubSubnet2)
        ))

        self.template.add_output(Output(
            "RESTPrivSubnet1",
            Description="Loyalty On Demand Rest Private Subnet1",
            Value=Ref(self.RESTPrivSubnet1)
        ))

        self.template.add_output(Output(
            "RESTPrivSubnet2",
            Description="Loyalty On Demand Rest Private Subnet2",
            Value=Ref(self.RESTPrivSubnet2)
        ))

        self.template.add_output(Output(
            "AdminCidrBlock",
            Description="AdminCidrBlock for VPC",
            Value=Ref(self.AdminCidrBlock)
        ))

        self.template.add_output(Output(
            "EnvironmentArtifactsS3Bucket",
            Description="S3 Bucket for Environment Artifacts",
            Value=Ref(self.EnvironmentArtifactsBucket)
        ))


def sceptre_handler(sceptre_user_data):
    vpc = VPC(sceptre_user_data)
    return vpc.template.to_json()
