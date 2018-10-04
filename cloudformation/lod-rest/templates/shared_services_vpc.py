from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output
from troposphere.s3 import Bucket, s3_bucket_name, VersioningConfiguration
from troposphere.ssm import Parameter as SSMParameter


class SharedServicesVPC(BaseCloudFormation):
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

        self.PubSub1Cidr = self.template.add_parameter(Parameter(
            "PubSub1Cidr",
            Type="String",
        ))

        self.PubSub2Cidr = self.template.add_parameter(Parameter(
            "PubSub2Cidr",
            Type="String",
        ))

        self.PrivSub1Cidr = self.template.add_parameter(Parameter(
            "PrivSub1Cidr",
            Type="String",
        ))

        self.PrivSub2Cidr = self.template.add_parameter(Parameter(
            "PrivSub2Cidr",
            Type="String",
        ))


    def add_resources(self):
        """ Add All Cloudformation Resources. This will include vpc, igw, and any other network
        resources """
        self.vpc = self.template.add_resource(ec2.VPC(
            "VPC",
            CidrBlock=Ref(self.VpcCidr),
            EnableDnsSupport=True,
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-VPC"),
        ))

        self.PubSubnet1 = self.template.add_resource(ec2.Subnet(
            "PubSubnet1",
            CidrBlock=Ref(self.PubSub1Cidr),
            VpcId=Ref(self.vpc),
            AvailabilityZone="us-east-1a",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PubSubnet1"),
        ))

        self.PubSubnet2 = self.template.add_resource(ec2.Subnet(
            "PubSubnet2",
            VpcId=Ref(self.vpc),
            CidrBlock=Ref(self.PubSub2Cidr),
            AvailabilityZone="us-east-1b",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PubSubnet2"),
        ))

        self.PrivSubnet1 = self.template.add_resource(ec2.Subnet(
            "PrivSubnet1",
            VpcId=Ref(self.vpc),
            CidrBlock=Ref(self.PrivSub1Cidr),
            AvailabilityZone="us-east-1a",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PrivSubnet1"),
        ))

        self.PrivSubnet2 = self.template.add_resource(ec2.Subnet(
            "PrivSubnet2",
            CidrBlock=Ref(self.PrivSub2Cidr),
            VpcId=Ref(self.vpc),
            AvailabilityZone="us-east-1b",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PrivSubnet2"),
        ))

        self.IGW = self.template.add_resource(ec2.InternetGateway(
            "IGW",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-IGW"),
        ))

        self.IGWAttachment = self.template.add_resource(ec2.VPCGatewayAttachment(
            "IGWAttachment",
            VpcId=Ref(self.vpc),
            InternetGatewayId=Ref(self.IGW),
        ))

        self.EIP1 = self.template.add_resource(ec2.EIP(
            "EIP1",
            Domain="vpc",
        ))

        self.EIP2 = self.template.add_resource(ec2.EIP(
            "EIP2",
            Domain="vpc",
        ))

        self.NAT1 = self.template.add_resource(ec2.NatGateway(
            "NAT",
            AllocationId=GetAtt(self.EIP1, "AllocationId"),
            SubnetId=Ref(self.PubSubnet1),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-NAT1"),
        ))

        self.NAT2 = self.template.add_resource(ec2.NatGateway(
            "NAT2",
            AllocationId=GetAtt(self.EIP2, "AllocationId"),
            SubnetId=Ref(self.PubSubnet2),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-NAT2"),
        ))

        self.PrivRT1 = self.template.add_resource(ec2.RouteTable(
            "PrivRT1",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PRIVRT1"),
        ))

        self.PrivRT2 = self.template.add_resource(ec2.RouteTable(
            "PrivRT2",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PRIVRT2"),
        ))

        self.NatRoute = self.template.add_resource(ec2.Route(
            "NatRoute",
            RouteTableId=Ref(self.PrivRT1),
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId=Ref(self.NAT1),
        ))

        self.Nat2Route = self.template.add_resource(ec2.Route(
            "NatRoute2",
            RouteTableId=Ref(self.PrivRT2),
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId=Ref(self.NAT2),
        ))

        self.PrivRT1Association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PrivRT1Association",
            SubnetId=Ref(self.PrivSubnet1),
            RouteTableId=Ref(self.PrivRT1),
        ))

        self.PrivRT2Association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PrivRT2Association",
            SubnetId=Ref(self.PrivSubnet2),
            RouteTableId=Ref(self.PrivRT2),
        ))

        self.PubRT1 = self.template.add_resource(ec2.RouteTable(
            "PubRT1",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PUBRT1"),
        ))

        self.PubRT2 = self.template.add_resource(ec2.RouteTable(
            "PubRT2",
            VpcId=Ref(self.vpc),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-SS-PUBRT2"),
        ))

        self.PubRT1IGWattachment = self.template.add_resource(ec2.Route(
            "PubRT1IGWAttachment",
            DependsOn=["IGWAttachment"],
            RouteTableId=Ref(self.PubRT1),
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=Ref(self.IGW),
        ))

        self.PubRT2IGWattachment = self.template.add_resource(ec2.Route(
            "PubRT2IGWAttachment",
            DependsOn=["IGWAttachment"],
            RouteTableId=Ref(self.PubRT2),
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=Ref(self.IGW),
        ))

        self.PubRT1Association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PubRT1Associate",
            SubnetId=Ref(self.PubSubnet1),
            RouteTableId=Ref(self.PubRT1),
        ))

        self.PubRT2Asocation = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PubR2Associate",
            SubnetId=Ref(self.PubSubnet2),
            RouteTableId=Ref(self.PubRT2),
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "VpcId",
            Description="VpcId Output",
            Value=Ref(self.vpc)
        ))

        self.template.add_output(Output(
            "VpcCidr",
            Description="VpcId Cidr Block",
            Value=Ref(self.VpcCidr)
        ))

        self.template.add_output(Output(
            "PubSubnet1",
            Description="Shared Services Public Subnet 1",
            Value=Ref(self.PubSubnet1)
        ))

        self.template.add_output(Output(
            "PubSubnet2",
            Description="Loyalty On Demand  Public Subnet 2",
            Value=Ref(self.PubSubnet2)
        ))

        self.template.add_output(Output(
            "PrivSubnet1",
            Description="Shared Services Private Subnet1",
            Value=Ref(self.PrivSubnet1)
        ))

        self.template.add_output(Output(
            "PrivSubnet2",
            Description="Shared Services Private Subnet2",
            Value=Ref(self.PrivSubnet2)
        ))

        self.template.add_output(Output(
            "AdminCidrBlock",
            Description="Shared Services for VPC",
            Value=Ref(self.AdminCidrBlock)
        ))

        self.template.add_output(Output(
            "PrivateRouteTable1",
            Description="Private Route Table 1",
            Value=Ref(self.PrivRT1)
        ))

        self.template.add_output(Output(
            "PrivateRouteTable2",
            Description="Private Route Table 2",
            Value=Ref(self.PrivRT2)
        ))




def sceptre_handler(sceptre_user_data):
    ssvpc = SharedServicesVPC(sceptre_user_data)
    return ssvpc.template.to_json()
