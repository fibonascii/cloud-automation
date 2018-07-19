import requests
import json
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-p', '--procedure', type='string',
                  dest='procedure')
(options, args) = parser.parse_args()


def get_template_data():
    """Make request to API to return data for packer job"""
    response = requests.get('http://172.18.0.4:8000/api/procedures/{}'.format(options.procedure))
    if response.status_code == 200:
        return response.json()


def get_parameters_list(json_response):
    """Get a list of all the parameters for a given procedure and return the list"""
    parameter_list = []
    procedure_templates = json_response['procedures']['procedure_template']
    for template in procedure_templates:
        for parameters in template['template_parameters']:
            parameter_dict = {parameters['parameter_name']: parameters['parameter_value']}
            parameter_list.append(parameter_dict)

    return parameter_list


def create_vars_file(parameter_list):
    """Create a packer vars file from the parameter list"""
    vars_dict = {}
    for parameter in parameter_list:
        vars_dict.update(parameter)

    with open('vars_file.json', 'w') as vars_file:
        json.dump(vars_dict, vars_file)

    return vars_dict


if __name__ == '__main__':
    data = get_template_data()
    parameters = get_parameters_list(data)
    create_vars_file(parameters)
