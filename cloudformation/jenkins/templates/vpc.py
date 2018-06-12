from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output


class VPC(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
         self.VpcCidr = self.template.add_parameter(Parameter(
             "VpcCidr",
              Default="10.0.0.0/16",
              Type="String",
              Description="CIDR Address for instantiated VPC", 
        ))

         self.PublicSubnetA = self.template.add_parameter(Parameter(
             "PublicSubnetA",
              Default="10.0.10.0/24",
              Type="String",
              Description="CIDR Address for Public Subnet",
        ))
  
         self.PrivateSubnetA = self.template.add_parameter(Parameter(
             "PrivateSubnetA",
              Default="10.0.20.0/24",
              Type="String",
              Description="CIDR Address for Private Subnet",
        ))

         self.PublicSubnetB = self.template.add_parameter(Parameter(
             "PublicSubnetB",
             Default="10.0.30.0/24",
             Type="String",
             Description="CIDR Address for Public Subnet",
         ))

         self.PrivateSubnetB = self.template.add_parameter(Parameter(
             "PrivateSubnetB",
             Default="10.0.40.0/24",
             Type="String",
             Description="CIDR Address for Private Subnet",
         ))

         self.AvailabilityZoneA = self.template.add_parameter(Parameter(
             "AvailabilityZoneA",
             Default="us-east-2a",
             Type="String",
        ))

         self.AvailabilityZoneB = self.template.add_parameter(Parameter(
             "AvailabilityZoneB",
             Default="us-east-2b",
             Type="String",
        ))


    def add_resources(self):
        self.vpc = self.template.add_resource(ec2.VPC(
             "VPC",
             CidrBlock=Ref(self.VpcCidr),
             Tags=self.default_tags + Tags(
                                        Name=self.environment_name + "-VPC"),
        ))

        self.public_subneta = self.template.add_resource(ec2.Subnet(
            "PublicSubnet",
            CidrBlock=Ref(self.PublicSubnetA),
            VpcId=Ref(self.vpc),
            AvailabilityZone=Ref(self.AvailabilityZoneA),
            MapPublicIpOnLaunch=True,
            Tags=self.default_tags + Tags(
                                       Name=self.environment_name + "-PUBSUBA"),
        ))

        self.private_subneta = self.template.add_resource(ec2.Subnet(
            "PrivateSubnet",
            CidrBlock=Ref(self.PrivateSubnetA),
            VpcId=Ref(self.vpc),
            AvailabilityZone=Ref(self.AvailabilityZoneA),
            MapPublicIpOnLaunch=True,
            Tags=self.default_tags + Tags(
                                       Name=self.environment_name + "-PRIVSUBA"),
        ))

        self.public_subnetb = self.template.add_resource(ec2.Subnet(
            "PublicSubnet2",
            CidrBlock=Ref(self.PublicSubnetB),
            VpcId=Ref(self.vpc),
            AvailabilityZone=Ref(self.AvailabilityZoneB),
            MapPublicIpOnLaunch=True,
            Tags=self.default_tags + Tags(
                                       name=self.environment_name + "-PUBSUBB"
            ),
        ))

        self.private_subnetb = self.template.add_resource(ec2.Subnet(
            "PrivateSubnet2",
            CidrBlock=Ref(self.PrivateSubnetB),
            VpcId=Ref(self.vpc),
            AvailabilityZone=Ref(self.AvailabilityZoneB),
            MapPublicIpOnLaunch=True,
            Tags=self.default_tags + Tags(
                Name=self.environment_name + "-PRIVSUBB"),
        ))

        self.private_route_table = self.template.add_resource(ec2.RouteTable(
             "PrivateRouteTable",
              VpcId=Ref(self.vpc), 
              Tags=self.default_tags + Tags(
                                         Name=self.environment_name + "-PRIVRTBL"),
        ))

        self.public_route_table = self.template.add_resource(ec2.RouteTable(
            "PublicRouteTable",
             VpcId=Ref(self.vpc),
             Tags=self.default_tags + Tags(
                                        Name=self.environment_name + "-PUBRTBL"),
        ))

        self.igw = self.template.add_resource(ec2.InternetGateway(
             "InternetGateway", 
             Tags=self.default_tags + Tags(
                                        Name=self.environment_name + "-IGW"),
        ))

        self.attach_igw = self.template.add_resource(ec2.VPCGatewayAttachment(
             "IGWAttachment",
             VpcId=Ref(self.vpc),
             InternetGatewayId=Ref(self.igw),
        ))

        self.nat_eip = self.template.add_resource(ec2.EIP(
             "NatEIP",
             Domain="vpc",
        ))      

        self.nat = self.template.add_resource(ec2.NatGateway(
             "Nat",
             AllocationId=GetAtt(self.nat_eip, 'AllocationId'),
             SubnetId=Ref(self.public_subneta),
             Tags=self.default_tags + Tags(
                                        Name=self.environment_name + "-NAT"),
        ))

        self.nat_route = self.template.add_resource(ec2.Route(
            "PublicRoute",
            RouteTableId=Ref(self.private_route_table),
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=Ref(self.nat),
        ))

        self.igw_route = self.template.add_resource(ec2.Route(
            "InternetGatewayRoute",
            RouteTableId=Ref(self.public_route_table),
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=Ref(self.igw),

        ))

        self.private_subnet_association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PriSubnetAssociation",
            SubnetId=Ref(self.private_subneta),
            RouteTableId=Ref(self.private_route_table),
        ))

        self.public_subnet_association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PubSubnetAssociation",
            SubnetId=Ref(self.public_subneta),
            RouteTableId=Ref(self.public_route_table),
        ))
        """Start Block for Second group of Subnets"""

        self.private_route_tableb = self.template.add_resource(ec2.RouteTable(
            "PrivateRouteTableB",
            VpcId=Ref(self.vpc),
            Tags=self.default_tags + Tags(
                Name=self.environment_name + "-PRIVRTBLB"),
        ))

        self.public_route_tableb = self.template.add_resource(ec2.RouteTable(
            "PublicRouteTableB",
            VpcId=Ref(self.vpc),
            Tags=self.default_tags + Tags(
                Name=self.environment_name + "-PUBRTBLB"),
        ))


        self.nat_eipb = self.template.add_resource(ec2.EIP(
            "NatEIPB",
            Domain="vpc",
        ))

        self.natb = self.template.add_resource(ec2.NatGateway(
            "NatB",
            AllocationId=GetAtt(self.nat_eipb, 'AllocationId'),
            SubnetId=Ref(self.public_subnetb),
            Tags=self.default_tags + Tags(
                Name=self.environment_name + "-NATB"),
        ))

        self.nat_routeb = self.template.add_resource(ec2.Route(
            "PublicRouteB",
            RouteTableId=Ref(self.private_route_tableb),
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=Ref(self.natb),
        ))

        self.private_subnet_associationb = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PriSubnetAssociationB",
            SubnetId=Ref(self.private_subnetb),
            RouteTableId=Ref(self.private_route_tableb),
        ))

        self.public_subnet_associationb = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PubSubnetAssociationB",
            SubnetId=Ref(self.public_subnetb),
            RouteTableId=Ref(self.public_route_tableb),
        ))


    def add_outputs(self):
        self.VpcId = self.template.add_output(Output(
             "VpcId",
             Description="The ID for the created VPC",
             Value=Ref(self.vpc),
        ))

        self.PrivateSubnetA = self.template.add_output(Output(
            "PrivateSubnetA",
            Description="Jenkins PrivateSubnetA",
            Value=Ref(self.private_subneta),
        ))

        self.PrivateSubnetB = self.template.add_output(Output(
            "PrivateSubnet2",
            Description="Jenkins PrivateSubnetB",
            Value=Ref(self.private_subnetb),
        ))

        self.PublicSubnetA = self.template.add_output(Output(
            "PublicSubnetA",
            Description="Jenkins PublicSubnetA",
            Value=Ref(self.public_subneta),
        ))

        self.PublicSubnetB = self.template.add_output(Output(
            "PublicSubnet2",
            Description="Jenkins PublicSubnetB",
            Value=Ref(self.public_subnetb),
        ))

        self.NatGateway = self.template.add_output(Output(
            "NatGateway",
            Description="NatGateway",
            Value=Ref(self.nat),
        ))

        self.NatGatewayB = self.template.add_output(Output(
            "NatGatewayB",
            Description="NatGateway",
            Value=Ref(self.natb),
        ))

        self.AvailabilityZoneA = self.template.add_output(Output(
            "AvailabilityZone1",
            Description="AvailabilityZone1",
            Value=Ref(self.AvailabilityZoneA)
        ))

        self.AvailabilityZoneB = self.template.add_output(Output(
            "AvailabilityZone2",
            Description="AvailabilityZone2",
            Value=Ref(self.AvailabilityZoneB)
        ))


def sceptre_handler(sceptre_user_data):
    vpc = VPC(sceptre_user_data)
    return vpc.template.to_json()
