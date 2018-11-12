from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output
from troposphere.rds import DBInstance, DBSubnetGroup

class Database(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.base_tags = Tags(
            ResourceOwner="ProductDevelopment",
            Environment="Development",
        )
        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):

        self.VpcId = self.template.add_parameter(Parameter(
            "VpcId",
            Type="String",
        ))

        self.ApiServerEC2SecurityGroup = self.template.add_parameter(Parameter(
            "ApiServerEC2SecurityGroup",
            Type="String",
        ))

        self.LoyaltyNavigatorEC2SecurityGroup = self.template.add_parameter(Parameter(
            "LoyaltyNavigatorEC2SecurityGroup",
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

        self.OracleRestDBUsername = self.template.add_parameter(Parameter(
            "OracleRestDBUsername",
            Type="String",
        ))

        self.OracleRestDBName = self.template.add_parameter(Parameter(
            "OracleRestDBName",
            Type="String",
        ))

        self.OracleRestDBClass = self.template.add_parameter(Parameter(
            "OracleRestDBClass",
            Type="String",
        ))

        self.OracleRestDBAllocatedStorage = self.template.add_parameter(Parameter(
            "OracleRestDBAllocatedStorage",
            Type="String",
        ))

        self.OracleRestDBStorageType = self.template.add_parameter(Parameter(
            "OracleRestDBStorageType",
            Type="String",
        ))

        self.OracleRestDBIOPS = self.template.add_parameter(Parameter(
            "OracleRestDBIOPS",
            Type="String",
        ))

        self.OracleRestDBPassword = self.template.add_parameter(Parameter(
            "OracleRestDBPassword",
            Type="String",
        ))

        self.OracleDBSnapshotArn = self.template.add_parameter(Parameter(
            "OracleDBSnapshotArn",
            Type="String",
        ))

        self.OracleDBParameterGroup = self.template.add_parameter(Parameter(
            "OracleDBParameterGroup",
            Type="String",
        ))

        self.DatabaseBaseFrameworkScriptsLocation = self.template.add_parameter(Parameter(
            "DatabaseBaseFrameworkScriptsLocation",
            Type="String",
        ))

        self.DatabaseReleaseFrameworkScriptsLocation = self.template.add_parameter(Parameter(
            "DatabaseReleaseFrameworkScriptsLocation",
            Type="String",
        ))

        self.SSEksWorkerNodeEc2SG = self.template.add_parameter(Parameter(
            "SSEksWorkerNodeEc2SG",
            Type="String",
        ))

    def add_resources(self):
        
        self.OracleRestDBSecurityGroup = self.template.add_resource(ec2.SecurityGroup(
            "OracleRestDBSecurityGroup",
            GroupDescription="Allow access to db",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=1521,
                    ToPort=1521,
                    SourceSecurityGroupId=Ref(self.ApiServerEC2SecurityGroup),
                ),
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=1521,
                    ToPort=1521,
                    SourceSecurityGroupId=Ref(self.LoyaltyNavigatorEC2SecurityGroup),
                )],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-OracleRDSSG"),
            )) 

        self.OracleRestDBSubnetGroup = self.template.add_resource(DBSubnetGroup(
            "OracleRestDBSubnetGroup",
            DBSubnetGroupDescription="RDS DB Subnet Group",
            SubnetIds=[Ref(self.RESTPrivSubnet1), Ref(self.RESTPrivSubnet2)],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-OracleRDSSubnetGroup"),
        ))

        self.OracleRestDBInstance = self.template.add_resource(DBInstance(
            "OracleRestDBInstance",
            DBName=Ref(self.OracleRestDBName),
            DBInstanceIdentifier=Ref(self.OracleRestDBName),
            Engine="oracle-se2",
            MasterUsername=Ref(self.OracleRestDBUsername),
            DBInstanceClass=Ref(self.OracleRestDBClass),
            EngineVersion="12.1.0.2.v8",
            LicenseModel="license-included",
            BackupRetentionPeriod="0",
            DBSubnetGroupName=Ref(self.OracleRestDBSubnetGroup),
            VPCSecurityGroups=[Ref(self.OracleRestDBSecurityGroup)],
            AllocatedStorage=Ref(self.OracleRestDBAllocatedStorage),
            StorageType=Ref(self.OracleRestDBStorageType),
            Iops=Ref(self.OracleRestDBIOPS),
            MasterUserPassword=Ref(self.OracleRestDBPassword),
            DBParameterGroupName=Ref(self.OracleDBParameterGroup),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-OracleRDS"),
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "OracleRestDBSecurityGroup",
            Value=Ref(self.OracleRestDBSecurityGroup),
        ))

        self.template.add_output(Output(
            "DatabaseBaseFrameworkScriptsLocation",
            Value=Ref(self.DatabaseBaseFrameworkScriptsLocation),
        ))

        self.template.add_output(Output(
            "DatabaseReleaseFrameworkScriptsLocation",
            Value=Ref(self.DatabaseReleaseFrameworkScriptsLocation),
        ))


def sceptre_handler(sceptre_user_data):
    database = Database(sceptre_user_data)
    return database.template.to_json()
