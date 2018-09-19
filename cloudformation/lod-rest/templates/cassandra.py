from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, GetAZs
from troposphere import elasticloadbalancing as elb, GetAZs
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
from troposphere.autoscaling import Tag as AutoScalingTag

class Cassandra(BaseCloudFormation):
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

        #AdminCidrBlock is VPC Output
        self.AdminCidrBlock = self.template.add_parameter(Parameter(
            "AdminCidrBlock",
            Type="String",
        ))
        
        self.CassandraImageId = self.template.add_parameter(Parameter(
            "CassandraImageId",
            Type="String",
        ))

        self.CassandraServerKeyName = self.template.add_parameter(Parameter(
            "CassandraServerKeyName",
            Type="String",
        ))

        self.CassandraServerInstanceType = self.template.add_parameter(Parameter(
            "CassandraServerInstanceType",
            Type="String",
        ))

        self.CassandraServerIAMInstanceProfile = self.template.add_parameter(Parameter(
            "CassandraServerIAMInstanceProfile",
            Type="String",
        ))

        self.CassandraServerSeedList = self.template.add_parameter(Parameter(
            "CassandraServerSeedList",
            Type="String",
        ))

        # RESTPrivSubnet1 is VPC Output
        self.RESTPrivSubnet1 = self.template.add_parameter(Parameter(
            "RESTPrivSubnet1",
            Type="String",
        ))

        # RESTPubSubnet1 is VPC Output
        self.RESTPubSubnet1 = self.template.add_parameter(Parameter(
            "RESTPubSubnet1",
            Type="String",
        ))

    def add_resources(self):
        
        self.CassandraPublicLBSG = self.template.add_resource(ec2.SecurityGroup(
            "CassandraPublicLBSG",
            GroupDescription="Loadbalancer Security Group For Cassandra Public LB",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    CidrIp=Ref(self.AdminCidrBlock),
                ),
            ],
                Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraPublicLBSG"),

            ))

        self.CassandraSG = self.template.add_resource(ec2.SecurityGroup(
            "CassandraSG",
            GroupDescription="Allow communication between Cassandra Seed and Non-Seed Nodes",
            VpcId=Ref(self.VpcId),
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort=22,
                    ToPort=22,
                    SourceSecurityGroupId=Ref(self.CassandraPublicLBSG),
                ),
            ],

            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraEc2SG"),
        ))

        self.CassandraSGInterNodeCommunicationIngress = self.template.add_resource(ec2.SecurityGroupIngress(
            "CassandraSGInterNodeCommunicationIngress",
            DependsOn=self.CassandraSG,
            GroupId=Ref(self.CassandraSG),
            IpProtocol="tcp",
            FromPort=7000,
            ToPort=7001,
            SourceSecurityGroupId=Ref(self.CassandraSG),
        ))

        self.CassandraSeedNetworkInterface = self.template.add_resource(ec2.NetworkInterface(
            "Eth0",
            Description="eth0",
            GroupSet=[Ref(self.CassandraSG)],
            SubnetId=Ref(self.RESTPrivSubnet1),
            PrivateIpAddress="10.0.1.132",
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraSeedNetworkInterface"),
        ))

        self.CassandraSeed1 = self.template.add_resource(ec2.Instance(
            "CassandraSeed1",
            ImageId=Ref(self.CassandraImageId),
            KeyName=Ref(self.CassandraServerKeyName),
            InstanceType=Ref(self.CassandraServerInstanceType),
            IamInstanceProfile=Ref(self.CassandraServerIAMInstanceProfile),
            NetworkInterfaces=[
                ec2.NetworkInterfaceProperty(
                    NetworkInterfaceId=Ref(self.CassandraSeedNetworkInterface),
                    DeviceIndex="0",
                    ),
            ],
            UserData=Base64(Join('', [
            "#!/bin/bash -x\n",
            "export NODE_IP=`hostname -I`\n",
            "export SEED_LIST=\"10.0.1.132\"\n",
            "export CASSANDRA_YML=\"/etc/cassandra/conf/cassandra.yaml\"\n",
            "export CLUSTER_NAME=\"devops_cluster\"\n",
            "export SNITCH_TYPE=\"Ec2Snitch\"\n",
            "sed -i \"/cluster_name:/c\\cluster_name: \\'${CLUSTER_NAME}\\'\"  ${CASSANDRA_YML}\n",
            "sed -i \"/- seeds:/c\\          - seeds: \\\"${SEED_LIST}\\\"\"     ${CASSANDRA_YML}\n",
            "sed -i \"/listen_address:/c\\listen_address: ${NODE_IP}\"       ${CASSANDRA_YML}\n",
            "sed -i \"/rpc_address:/c\\rpc_address: ${NODE_IP}\"             ${CASSANDRA_YML}\n",
            "sed -i \"/endpoint_snitch:/c\\endpoint_snitch: ${SNITCH_TYPE}\" ${CASSANDRA_YML}\n",
            "sed -i \"/authenticator: AllowAllAuthenticator/c\\authenticator: PasswordAuthenticator\" ${CASSANDRA_YML}\n"
            "echo 'auto_bootstrap: false' >> ${CASSANDRA_YML}\n",
            "service cassandra start\n" ])),
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraSeed-1-Ec2"),
        ))

        self.CassandraPublicLoadBalancer = self.template.add_resource(elb.LoadBalancer(
            "CassandraPublicLoadBalancer",
            LoadBalancerName=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraNonSeedPubLB",
            Scheme="internet-facing",
            Listeners=[
                elb.Listener(
                    LoadBalancerPort="22",
                    InstancePort="22",
                    Protocol="TCP",
                    InstanceProtocol="TCP",
                )
            ],
            Instances=[],
            SecurityGroups=[Ref(self.CassandraPublicLBSG)],
            Subnets=[Ref(self.RESTPubSubnet1)],
            Tags=self.base_tags + Tags(Name=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraNonSeedPubLB"),
        ))

        self.CassandraNonSeedLaunchConfiguration = self.template.add_resource(LaunchConfiguration(
            "CassandraNonSeedLaunchConfiguration",
            ImageId=Ref(self.CassandraImageId),
            InstanceType=Ref(self.CassandraServerInstanceType),
            IamInstanceProfile=Ref(self.CassandraServerIAMInstanceProfile),
            KeyName=Ref(self.CassandraServerKeyName),
            SecurityGroups=[Ref(self.CassandraSG)],
            UserData=Base64(Join('', [
            "#!/bin/bash -x\n",
            "export NODE_IP=`hostname -I`\n",
            "export SEED_LIST=\"10.0.1.132\"\n",
            "export CASSANDRA_YML=\"/etc/cassandra/conf/cassandra.yaml\"\n",
            "export CLUSTER_NAME=\"devoops_cluster\"\n",
            "export SNITCH_TYPE=\"Ec2Snitch\"\n",
            "sed -i \"/cluster_name:/c\\cluster_name: \\'${CLUSTER_NAME}\\'\"  ${CASSANDRA_YML}\n",
            "sed -i \"/- seeds:/c\\          - seeds: \\\"${SEED_LIST}\\\"\"     ${CASSANDRA_YML}\n",
            "sed -i \"/listen_address:/c\\listen_address: ${NODE_IP}\"       ${CASSANDRA_YML}\n",
            "sed -i \"/rpc_address:/c\\rpc_address: ${NODE_IP}\"             ${CASSANDRA_YML}\n",
            "sed -i \"/endpoint_snitch:/c\\endpoint_snitch: ${SNITCH_TYPE}\" ${CASSANDRA_YML}\n",
            "sed -i \"/authenticator: AllowAllAuthenticator/c\\authenticator: PasswordAuthenticator\" ${CASSANDRA_YML}\n",
            "echo 'auto_bootstrap: false' >> ${CASSANDRA_YML}\n",
            "service cassandra start\n"
            ])),
        ))

        self.CassandraNonSeedAutoScalingGroup = self.template.add_resource(AutoScalingGroup(
            "CassandraNonSeedAutoscalingGroup",
            AutoScalingGroupName=self.environment_parameters["ClientEnvironmentKey"] + "-CassandraNonSeedAutoScalingGroup",
            LaunchConfigurationName=Ref(self.CassandraNonSeedLaunchConfiguration),
            LoadBalancerNames=[Ref(self.CassandraPublicLoadBalancer)],
            MaxSize="1",
            MinSize="1",
            DesiredCapacity="1",
            VPCZoneIdentifier=[Ref(self.RESTPrivSubnet1)],
            Tags=[
                AutoScalingTag("Name", self.environment_parameters["ClientEnvironmentKey"] + "-CassandraNonSeedEc2",True),
                AutoScalingTag("Environment", self.environment_parameters["EnvironmentName"], True),
                AutoScalingTag("ResourceOwner", self.environment_parameters["ResourceOwner"], True),
                AutoScalingTag("ClientCode", self.environment_parameters["ClientEnvironmentKey"], True),
            ],
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "CassandraSG",
            Value=Ref(self.CassandraSG)
        ))

        self.template.add_output(Output(
            "CassandraServerSeedList",
            Value=Ref(self.CassandraServerSeedList)
        ))

def sceptre_handler(sceptre_user_data):
    cassandra = Cassandra(sceptre_user_data)
    return cassandra.template.to_json()
