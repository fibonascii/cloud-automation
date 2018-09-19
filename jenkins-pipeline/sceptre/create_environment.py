#!/usr/bin/env python3 -u
import os
import sys
from optparse import OptionParser
import requests
from sceptreutils.handlers import TemplateHandler
from sceptre.environment import Environment as environ


parser = OptionParser()
parser.add_option('-e', '--environment', type='string',
                  dest='environment', default='dev')
parser.add_option('-r', '--region', type='string',
                  dest='region', default='us-east-1')
parser.add_option('-p', '--procedure', type='string',
                  dest='procedure')

(options, args) = parser.parse_args()

sceptre_directory = os.path.join(os.environ['JENKINS_HOME'], 'workspace/CreateEnvironment/cloudformation')


def get_response_data():
    """Call API for procedure using Jenkins Parameter
       Return procedure back as JSON"""
    response = requests.get('http://172.18.0.4:8000/api/procedures/{}'.format(options.procedure))
    if response.status_code == 200:
        return response.json()


def generate_templates(response_data):
    """Iterate through procedure generating sceptre config files from procedure parameters"""

    handler = TemplateHandler(project_path=os.path.join(sceptre_directory, str(options.procedure).lower()),
                              environment_name=options.environment,
                              data=response_data)

    handler.generate_templates()

    return handler


def launch_environment():
    """Launch Cloudformation environment via sceptre using newly generated files"""

    # Initialize the root level project config.yaml
    config_data = {'project_code': str(options.procedure).lower(),
                   'region': options.region}

    # Create sceptre environment object using api response and config.yaml values
    env = environ(sceptre_dir=os.path.join(sceptre_directory, str(options.procedure).lower()),
                  environment_path=options.environment, options=config_data)

    # Check that the environment is a leaf env (reference sceptre docs) and launch the env. If a stack fails exit script
    if env.is_leaf:
        environments = env.launch()
        for stack_name, status in environments.items():
            if 'failed' in status:
                print(environments)
                sys.exit(1)
            else:
                return environments


if __name__ == '__main__':
    data = get_response_data()
    templates = generate_templates(data)
    launch_environment()
