import sys
from sceptre.environment import Environment as environ
from optparse import OptionParser
from sceptreutils import TemplateHandler

parser = OptionParser()
parser.add_option('-p', '--path', type='string',
                  dest='project_path', default='jenkins')
parser.add_option('-e', '--environment', type='string',
                  dest='environment', default='dev')
parser.add_option('-r', '--region', type='string',
                  dest='region', default='us-east-1')

(options, args) = parser.parse_args()

if not options.project_path and options.environment and options.region:
    print("Missing required command line arguments")
    sys.exit(1)


config_data = {'project_code': 'jenkins' + '-rkirby',
               'region': options.region}

response = {"ProductCode": "LodRest", "EnvironmentType": "Production", "Jobs": [{"JobType": "Sceptre", "JobTemplates": [{"TemplateName": "templates/vpc.py", "ParameterFiles": [{"Parameters": [{"VpcCidr": "10.0.0.0/16"}, {"PublicSubnetA": "10.0.10.0/24"}, {"PrivateSubnetA": "10.0.20.0/24"}, {"PublicSubnetB": "10.0.30.0/24"}, {"AvailabilityZoneA": "us-east-1a"}, {"AvailabilityZoneB": "us-east-1b"}]}]}, {"TemplateName": "templates/securitygroups.py", "ParameterFiles": [{"Parameters": [{"NatGateway": "!stack_output vpc::NatGateway"}, {"VpcId": "!stack_output vpc::VpcId"}, {"PublicIP": "204.57.87.152/32"}]}]}, {"TemplateName": "templates/instances.py", "ParameterFiles": [{"Parameters": [{"LoadBalancerName": "Jenkins-Test-Rkirby"}, {"AMIID": "ami-56a5f329"}, {"SLAVEAMIID": "ami-a5a6f0da"}, {"PublicSubnet1": "!stack_output vpc::PublicSubnetA"}, {"PrivateSubnet1": "!stack_output vpc::PrivateSubnetA"}, {"KeyPair": "jenkins-development"}, {"LoadBalancerSecurityGroup": "!stack_output securitygroups::LoadBalancerSecurityGroup"}, {"InstanceSecurityGroup": "!stack_output securitygroups::InstanceSecurityGroup"}, {"SlaveInstanceSecurityGroup": "!stack_output securitygroups::SlaveInstanceSecurityGroup"}, {"AvailabilityZoneA": "!stack_output vpc::AvailabilityZone1"}, {"AvailabilityZoneB": "!stack_output vpc::AvailabilityZone2"}]}]}]}]}
env = environ(sceptre_dir=options.project_path, environment_path=options.environment, options=config_data)

handler = TemplateHandler(project_path=options.project_path,
                          environment_name=options.environment,
                          data=response)
handler.generate_templates()


if env.is_leaf:
    environments = env.launch()
    for stack_name, status in environments.items():
        if 'failed' in status:
            print(environments)
            sys.exit(1)