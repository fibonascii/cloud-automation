import boto3
from sceptre.environment import Environment as Environ
from optparse import OptionParser
from jinja2 import Template, Environment, FileSystemLoader
from fabric import Connection
import os
import logging



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
    """ Fetch the SSM Parameters needed to template out to JMX File """
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


    parameter_dict = {}
    parameter_dict['JMeterJMXFilename'] = parameters['Parameters'][0]['Value'] 
    parameter_dict['JMeterTestExecutionLength'] = parameters['Parameters'][1]['Value'] 
    parameter_dict['restApiPrefix'] = parameters['Parameters'][2]['Value'] 
    parameter_dict['restKongConsumerClientSecret'] = parameters['Parameters'][3]['Value'] 
    parameter_dict['restKongConsumerClientId'] = parameters['Parameters'][4]['Value'] 

    return parameter_dict


def get_environment_stack_outputs():
    """ Use the Sceptre API to grab stack outputs from Kong and Jmeter """

    env = Environ(sceptre_dir=os.path.join(cloudformation_root, str(options.procedure)),
                    environment_path=options.environment)
    stack = env.stacks['jmeter']
    outputs = stack.describe_outputs()

    stack_output_dict = {}
    for output in outputs:
        if output['OutputKey'] == 'JmeterMasterPublicLoadBalancerDnsName':
            stack_output_dict[output['OutputKey']] = output['OutputValue'] 
    
    stack = env.stacks['kong']
    outputs = stack.describe_outputs()
    for output in outputs:
        if output['OutputKey'] == 'KongPublicLoadBalancerDNS':
            stack_output_dict[output['OutputKey']] = output['OutputValue'] 

    return stack_output_dict


def create_jmx_file(parameters, outputs):
    """ Updated the parameters dictionary with stack outputs, and render the JMX template with parameters
    and write the file to the filesystem """
    
    parameters.update(outputs)
    j2_env = Environment(loader=FileSystemLoader(os.getcwd()), trim_blocks=True)
    template = j2_env.get_template('ProdDev-Latest_LoadTest.jmx.j2')
    rendered = template.render(parameters)  
    with open(parameters['JMeterJMXFilename'], 'w') as file:
        file.write(rendered)


def fetch_jmeter_server_details():
    """ Use Boto3 to fetch the private IP of master and slave and the name of the ssh key to
    connect to the servers """
    pass


def execute_jmeter_tests(parameters, outputs):
    """ Connect to the JMeter Master and Slave using the values grabbed in other steps
    and execute the JMeter Load Testsi """

    JMeterMasterELB = outputs['JmeterMasterPublicLoadBalancerDnsName']
    JMeterMasterPrivateIP = '10.0.1.44'
    JMeterSlaveELB = 'U1NIKE-JMeterSlavePubELB-86711008.us-east-1.elb.amazonaws.com'
#    JMeterResultsFile = parameters['JMeterJMXResultsFileName']
    JMeterResultsFile = 'myresultsfile.jlt' 
    JMXFile = parameters['JMeterJMXFilename']
    connect_kwargs = {"key_filename":['jenkins-development.pem']}

    launch_slave = './apache-jmeter-4.0/bin/jmeter-server >&- 2>&- <&- &'
    
    launch_master = './apache-jmeter-4.0/bin/jmeter.sh -n -t ~/{} -R {} -l ~/{} -Djava.rmi.server.hostname={}'.format(
            JMXFile, JMeterMasterELB, JMeterResultsFile, JMeterMasterPrivateIP) 

    with Connection(JMeterSlaveELB, user='ec2-user', connect_kwargs=connect_kwargs) as conn:
            conn.run(launch_slave)
    
    with Connection(JMeterMasterELB, user='ec2-user', connect_kwargs=connect_kwargs) as conn:
            conn.put('{}'.format(JMXFile))
            conn.run(launch_master)


if __name__ == '__main__':
    parameters = get_ssm_parameters(client_code)
    outputs = get_environment_stack_outputs()
    create_jmx_file(parameters, outputs)
    execute_jmeter_tests(parameters, outputs)
