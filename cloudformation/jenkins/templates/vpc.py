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
          
         self.VpcName = self.template.add_parameter(Parameter(
            "VpcName",
            Type="String"
        ))  

         self.IgwName = self.template.add_parameter(Parameter(
           "IgwName",
           Type="String"
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

         self.AvailabilityZoneA = self.template.add_parameter(Parameter(
             "AvailabilityZone1",
             Default="us-east-1a",
             Type="String",
        ))

         self.AvailabilityZoneB = self.template.add_parameter(Parameter(
             "AvailabilityZone2",
             Default="us-east-1b",
             Type="String",
        ))


    def add_resources(self):
        self.vpc = self.template.add_resource(ec2.VPC(
             "VPC",
             CidrBlock=Ref(self.VpcCidr),
             Tags=self.default_tags + Tags(
                                        Name=Ref(self.VpcName)),
        ))

        self.public_subnet = self.template.add_resource(ec2.Subnet(
            "PublicSubnet",
            CidrBlock=Ref(self.PublicSubnetA),
            VpcId=Ref(self.vpc),
            AvailabilityZone=Ref(self.AvailabilityZoneA),
            MapPublicIpOnLaunch=True,
            Tags=self.default_tags,
        ))

        self.private_subnet = self.template.add_resource(ec2.Subnet(
            "PrivateSubnet",
            CidrBlock=Ref(self.PrivateSubnetA),
            VpcId=Ref(self.vpc),
            AvailabilityZone=Ref(self.AvailabilityZoneA),
            MapPublicIpOnLaunch=True,
            Tags=self.default_tags,
        ))

        self.private_route_table = self.template.add_resource(ec2.RouteTable(
             "PrivateRouteTable",
              VpcId=Ref(self.vpc), 
              Tags=self.default_tags,
        ))

        self.public_route_table = self.template.add_resource(ec2.RouteTable(
            "PublicRouteTable",
             VpcId=Ref(self.vpc),
             Tags=self.default_tags,
        ))

        self.igw = self.template.add_resource(ec2.InternetGateway(
             "InternetGateway", 
             Tags=self.default_tags + Tags(
                                        Name=Ref(self.IgwName)),
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
             SubnetId=Ref(self.public_subnet),
             Tags=self.default_tags
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
            SubnetId=Ref(self.private_subnet),
            RouteTableId=Ref(self.private_route_table),
        ))

        self.public_subnet_association = self.template.add_resource(ec2.SubnetRouteTableAssociation(
            "PubSubnetAssociation",
            SubnetId=Ref(self.public_subnet),
            RouteTableId=Ref(self.public_route_table),
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
            Value=Ref(self.private_subnet),
        ))

        self.PrivateSubnetA = self.template.add_output(Output(
            "PublicSubnetA",
            Description="Jenkins PublicSubnetA",
            Value=Ref(self.public_subnet),
        ))

        self.NatGateway = self.template.add_output(Output(
            "NatGateway",
            Description="NatGateway",
            Value=Ref(self.nat),
        ))



def sceptre_handler(sceptre_user_data):
    vpc = VPC(sceptre_user_data)
    return vpc.template.to_json()
