import logging
from botocore.vendored import requests
import boto3
import urllib
import json
import zipfile
import tempfile
import re
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create S3 client
s3 = boto3.client('s3')

def fetch_jenkins_parameters_from_event(event):
    file_name = event['Records'][0]['s3']['object']['key']
    bucket_name = event['Records'][0]['s3']['bucket']['name']

    version_numbers = re.search('(v\d+(?:\.\d+)*)(?:[-]([A-Za-z]+))?((?:\.\d+)*)\.zip', str(file_name))

    rest_release = {
                        "VERSION_NUMBER": version_numbers.group(1),
                        "RELEASE_TYPE": version_numbers.group(2),
                        "RELEASE_SEQUENCE": version_numbers.group(3).replace(".", ""),
                        "RELEASE_NAME": file_name.split('/')[2].replace(".zip", ""),
                        "S3_BUCKET_NAME": bucket_name,
                        "KEY_PREFIX": file_name.replace(file_name.split('/')[2], "")
    }

    return rest_release


def fetch_jenkins_parameters_from_archive_metadata(event, metadata_received):
    key = event['Records'][0]['s3']['object']['key']
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    print(key)
    print(bucket_name)
    tmp_file = tempfile.NamedTemporaryFile()
    with tempfile.NamedTemporaryFile() as tmp_file:
        s3.download_file(bucket_name, key, tmp_file.name)
        with zipfile.ZipFile(tmp_file.name, 'r') as archive:
            release_metadata_file_path = "release_metadata/release-metadata.json"
            print(tmp_file.name)
            print(release_metadata_file_path)
            if release_metadata_file_path in archive.namelist():
                print("Release Meta-Data File Received.")
                release_metadata_file = archive.read(release_metadata_file_path)
                release_metadata_json = json.loads(release_metadata_file)
                print("Release Meta Data File")
                print(release_metadata_json)
                metadata_received = True
                rest_release = {
                    "VERSION_NUMBER": vrelease_metadata_json['Releases'][0]['Release']['VersionNumber'],
                    "RELEASE_TYPE": elease_metadata_json['Releases'][0]['Release']['Type'],
                    "RELEASE_SEQUENCE": velease_metadata_json['Releases'][0]['Release']['Sequence'],
                    "RELEASE_NAME": elease_metadata_json['Releases'][0]['Release']['Name'],
                    "S3_BUCKET_NAME": bucket_name,
                    "KEY_PREFIX": release_metadata_json['Releases'][0]['Archive']['KeyPrefix'],
                    "ClientCode": release_metadata_json['Releases'][0]['Client']['ClientCode'],
                    "VersionNumber": release_metadata_json['Releases'][0]['Release']['VersionNumber'],
                    "KeyPrefix": release_metadata_json['Releases'][0]['Archive']['KeyPrefix'],
                    "AccountNumber": release_metadata_json['Releases'][0]['TargetEnvironment']['AccountNumber'],
                    "RefComponentId": release_metadata_json['Releases'][0]['Component']['RefComponentId']
                }
                return rest_release
            else:
                print("Release Meta-Data File Not Received.")
                metadata_received = False


def trigger_build(rest_release):
    username = os.environ['USERNAME']
    token = os.environ['API_TOKEN']
    encoded_data = urllib.parse.urlencode(rest_release)
    parameters = urllib.parse.quote_plus(encoded_data)
    url = '{}/job/PackerImageBuild/buildWithParameters?{}'.format(os.environ['LOAD_BALANCER'], parameters)
    response = requests.post(url, data=rest_release, auth=(username, token))

    return response.status_code


def lambda_handler(event, context):
    metadata_received = False
    rest_release = fetch_jenkins_parameters_from_archive_metadata(event, metadata_received)

    if not metadata_received:
        rest_release = fetch_jenkins_parameters_from_event(event)

    logger.info(rest_release)
    build = trigger_build(rest_release)

    return build
