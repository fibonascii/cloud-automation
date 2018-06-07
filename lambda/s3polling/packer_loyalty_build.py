import logging
from botocore.vendored import requests
import urllib
import json
import re
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def parse_version_numbers(file_name):
    version_numbers = re.search('(v\d+(?:\.\d+)*)(?:[-]([A-Za-z]+))?((?:\.\d+)*)\.zip', str(file_name))
    
    rest_release = {
                        "VERSION_NUMBER": version_numbers.group(1),
                        "RELEASE_TYPE": version_numbers.group(2),
                        "RELEASE_SEQUENCE": version_numbers.group(3).replace(".", "") }
 
    return rest_release    
    

def trigger_build(rest_release):
    username = os.environ['USERNAME']
    token = os.environ['API_TOKEN']
    encoded_data = urllib.parse.urlencode(rest_release)
    parameters = urllib.parse.quote_plus(encoded_data)
    url = '{}/job/PackerImageBuild/buildWithParameters?{}'.format(os.environ['LOAD_BALANCER'], parameters)
    response = requests.post(url, data=rest_release, auth=(username, token))

    return response.status_code
    
    
def lambda_handler(event, context):
    file_name = event['Records'][0]['s3']['object']['key']
    rest_release = parse_version_numbers(file_name)
    logger.info(rest_release)
    build = trigger_build(rest_release)

    return build
