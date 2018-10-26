import boto3
from sceptre.environment import Environment
from optparse import OptionParser
import os

parser = OptionParser()
parser.add_option('-p', '--procedure', type="string",
                dest="procedure", default="lod-rest")
parser.add_option('-e', '--environment', type="string",
                dest="environment", default="dev")

(options, args) = parser.parse_args()

client_code = 'U1NIKE'
#cloudformation_root = os.path.join(os.environ['JENKINS_HOME'], 'workspace/ValidateBuild/cloudformation')
cloudformation_root = '/Users/rkirby/repo/cloud-automation/cloudformation' 

def get_ssm_parameters(client_code):
    client = boto3.client('ssm')
    parameters = client.get_parameters(
            Names=[
                '{}-JMeterJMXFileName'.format(client_code),
                '{}-JMeterJMXResultsFileName'.format(client_code),
                '{}-JMeterTestExecutionLength'.format(client_code),
                '{}-restApiPrefix'.format(client_code),
                '{}-restKongConsumerClientSecret'.format(client_code),
                '{}-restKongConsumerClientId'.format(client_code),
                ],
            WithDecryption=True
        )

    parameter_list = []
    parameter_list.append(parameters['Parameters'][0]['Value'])
    parameter_list.append(parameters['Parameters'][1]['Value'])
    parameter_list.append(parameters['Parameters'][2]['Value'])
    parameter_list.append(parameters['Parameters'][3]['Value'])
    parameter_list.append(parameters['Parameters'][4]['Value'])

    return parameter_list

def get_environment_stack_outputs():
    env = Environment(sceptre_dir=os.path.join(cloudformation_root, str(options.procedure)),
                    environment_path=options.environment)
    stack = env.stacks['jmeter']
    outputs = stack.describe_outputs()

    stack_output_list = []
    for output in outputs:
        if output['OutputKey'] == 'JmeterMasterPublicLoadBalancerDnsName':
            stack_output_list.append(output['OutputValue']) 
    
    stack = env.stacks['kong']
    outputs = stack.describe_outputs()
    for output in outputs:
        if output['OutputKey'] == 'KongPublicLoadBalancerDNS':
            stack_output_list.append(output['OutputValue']) 

    return stack_output_list

    
parameters = get_ssm_parameters(client_code)
outputs = get_environment_stack_outputs()
print(outputs)
print(parameters)
