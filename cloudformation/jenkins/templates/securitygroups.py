from troposphere import ec2, Ref, Output, Parameter
from base import BaseCloudFormation

class SecurityGroups(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
        self.PublicIP = self.template.add_parameter(Parameter(
            "PublicIP",
            Type="String",
            Default='204.57.87.152/32',
        ))

        self.NatGateway = self.template.add_parameter(Parameter(
            "NatGateway",
            Type="String",
        ))

        self.VPCId = self.template.add_parameter(Parameter(
            "VPCId",
            Type="String",
        ))

    def add_resources(self):
        self.LoadBalancerSecurityGroup = self.template.add_resource(ec2.SecurityGroup(
            "LoadBalancerSecurityGroup",
            GroupDescription="Jenkins Load Balancer Security Group",
            VpcId=Ref(self.VPCId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=80,
                    ToPort=80,
                    CidrIp=Ref(self.PublicIP),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=443,
                    ToPort=443,
                    CidrIp=Ref(self.PublicIP),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=22,
                    ToPort=22,
                    CidrIp=Ref(self.PublicIP),
                ),
            ]
        )
    )
        self.InstanceSecurityGroup = self.template.add_resource(ec2.SecurityGroup(
            "InstanceSecurityGroup",
            GroupDescription="Security Group For Dev Jenkins Instance",
            VpcId=Ref(self.VPCId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=8080,
                    ToPort=8080,
                    SourceSecurityGroupId=Ref(self.LoadBalancerSecurityGroup),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.LoadBalancerSecurityGroup),
                ),
            ]
        )
    )

            
    def add_outputs(self):
        self.LoadBalancerSecurityGroup = self.template.add_output(Output(
             "LoadBalancerSecurityGroup",
             Description="LoadBalancerSecurityGroup",
             Value=Ref(self.LoadBalancerSecurityGroup),
        ))

        self.InstanceSecurityGroup = self.template.add_output(Output(
            "InstanceSecurityGroup",
            Description="Instance Security Group",
            Value=Ref(self.InstanceSecurityGroup),
        ))

        
def sceptre_handler(sceptre_user_data):
    securitygroups = SecurityGroups(sceptre_user_data)
    return securitygroups.template.to_json()        

        
