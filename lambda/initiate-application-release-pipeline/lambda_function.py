import logging
from botocore.vendored import requests
import boto3
import urllib
import json
import zipfile
import tempfile
import re
import os
import operator

# Release Html Creation Modules
import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension
import datetime
from jinja2 import Environment, FileSystemLoader
from flask import Markup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create S3 client
s3 = boto3.client('s3')


def lambda_handler(event, context):
    release_artifacts = fetch_release_artifacts_from_archive(event)
    release_details = fetch_release_details_from_release_metadata(event, release_artifacts['ReleaseMetadata'])
    render_release_page_html(release_artifacts['ReleaseNotes'], release_details)
    move_release_to_s3_destination(release_details)
    render_application_release_listing_page_html(release_details)
    jenkins_trigger_result = trigger_jenkins(release_details)

    logger.info(release_details)

    return jenkins_trigger_result


def fetch_release_artifacts_from_archive(event):
    """ Parse Metadata information from Release Files uploaded to S3"""
    release_artifacts = {}
    s3_file_key = event['Records'][0]['s3']['object']['key']
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    print(s3_file_key)
    print(s3_bucket)

    # Currently, hardcoded List of files we expect to receive as part of this request
    file_keys = ["release_metadata/release-metadata.json", "release_metadata/ReleaseNotes.md"]
    extracted_files = extract_files_from_s3_archive(s3_bucket, s3_file_key, file_keys)

    release_artifacts["ReleaseMetadata"] = extracted_files[0]
    release_artifacts["ReleaseNotes"] = extracted_files[1]

    return release_artifacts


def extract_files_from_s3_archive(s3_bucket, s3_file_key, file_keys):
    """ Download File from S3 Bucket Extract Files from Zip Archive and return in List"""
    extracted_files = []
    with tempfile.NamedTemporaryFile() as release_archive:
        s3.download_file(s3_bucket, s3_file_key, release_archive.name)
        with zipfile.ZipFile(release_archive.name, 'r') as tmp_archive:
            for key in file_keys:
                if key in tmp_archive.namelist():
                    tmp_file = tmp_archive.read(key)
                    extracted_files.append(tmp_file)
                else:
                    raise ValueError(key + "does not exist in the archive: " + s3_file_key)

            return extracted_files


def fetch_release_details_from_release_metadata(event, release_metadata_file):
    """ Extract Values from Release MetaData JSON and Place into Dictionary for further use"""
    s3_file_key = event['Records'][0]['s3']['object']['key']
    s3_bucket = event['Records'][0]['s3']['bucket']['name']

    release_metadata_json = json.loads(release_metadata_file)
    print("Release Meta Data File")
    print(release_metadata_json)

    release_details = {
        "CLIENT_CODE": release_metadata_json['Releases'][0]['Client']['ClientCode'],
        "APPLICATION_CODE": release_metadata_json['Releases'][0]['Application']['ApplicationCode'],
        "APPLICATION_DISPLAY_NAME": release_metadata_json['Releases'][0]['Application']['ApplicationDisplayName'],
        "S3_BUCKET_NAME": s3_bucket,
        "S3_FILE_KEY": s3_file_key,
        "APPLICATION_VERSION_NUMBER": release_metadata_json['Releases'][0]['Release']['VersionNumber'],
        "APPLICATION_RELEASE_TYPE": release_metadata_json['Releases'][0]['Release']['Type'],
        "APPLICATION_RELEASE_SEQUENCE": release_metadata_json['Releases'][0]['Release']['Sequence'],
        "APPLICATION_RELEASE_NAME": release_metadata_json['Releases'][0]['Release']['Name'],
        "RELEASE_DATE": release_metadata_json['Releases'][0]['Release']['Date'],
        "ARCHIVE_NAME": release_metadata_json['Releases'][0]['Archive']['ArchiveName']
        }
    release_details["APPLICATION_RELEASE_UPLOAD_KEY"] = release_details['CLIENT_CODE'] + \
        '/applications/' + \
        release_details['APPLICATION_CODE'] \
        + '/releases/'

    return release_details


def render_release_page_html(release_notes_file, release_details):
    """ Render the Client Application HTML for the specific Release triggered by this event"""
    # Convert ReleaseNotes to GitHub flavored MarkDown Syntax
    release_notes = Markup(markdown.markdown(release_notes_file.decode("utf-8"), extensions=[GithubFlavoredMarkdownExtension()]))
    # Convert Release Date Format
    release_date = datetime.datetime.strptime(release_details['RELEASE_DATE'], '%Y-%m-%d').strftime('%m/%d/%y')
    # Determine appropriate CSS based on release type
    release_version_type_css = release_type_css_switcher(release_details['APPLICATION_RELEASE_TYPE'])
    # Build S3 Release Download Link based on Release Details
    release_download_link = 'https://s3.amazonaws.com/' + release_details['S3_BUCKET_NAME'] + '/' \
                            + release_details['CLIENT_CODE'] + '/applications/' \
                            + release_details['APPLICATION_CODE'] + '/releases/' \
                            + release_details['APPLICATION_RELEASE_NAME'] + '.zip'

    # Set AMI Information - Pending
    release_ami_region = 'us-east-1'
    release_ami_identifier = 'Pending'
    release_ami_locator = 'state=pending'
    release_ami_link = 'https://console.aws.amazon.com/ec2/v2/home?region=' + release_ami_region + \
        '#Images:visibility=private-images;' + release_ami_locator + ';sort=desc:creationDate'

    # Render the template with the release details
    j2_env = Environment(loader=FileSystemLoader('templates'),
                         trim_blocks=True)

    rendered = j2_env.get_template('application-release-notes-template.html').render(**locals())

    # Push the rendered html page to S3 for consumption
    encoded_string = rendered.encode("utf-8")
    destination_key = release_details['CLIENT_CODE'] + '/applications/' + release_details['APPLICATION_CODE'] \
        + '/releases/' + release_details['APPLICATION_RELEASE_NAME'] + '-release-notes.html'

    put_release_html_in_s3_response = s3.put_object(Bucket=release_details['S3_BUCKET_NAME'], Key=destination_key, Body=encoded_string,
                                                    ContentType='text/html')
    logger.info(put_release_html_in_s3_response)
    return rendered


def render_application_release_listing_page_html(release_details):
    """ Render the Client Application HTML to List all available Releases and Push to S3"""

    # Build S3 Query Prefix to Look at the Specific Client and Application being released
    client_app_release_key_prefix = release_details['CLIENT_CODE'] + '/applications/' + \
        release_details['APPLICATION_CODE'] \
        + '/releases/'

    # Query S3 for all release pages to build an accurate list of currently available releases.
    release_list = fetch_all_application_releases(release_details['S3_BUCKET_NAME'], client_app_release_key_prefix)

    # Render the template with the results from the S3 Query
    j2_env = Environment(loader=FileSystemLoader('templates'),
                         trim_blocks=True)
    rendered = j2_env.get_template('application-release-listing-template.html').render(**locals())

    # Push the rendered html page to S3 for consumption
    encoded_string = rendered.encode("utf-8")
    destination_key = release_details['CLIENT_CODE'] + '/applications/' + release_details['APPLICATION_CODE'] \
        + '/releases/' + release_details['APPLICATION_CODE'] + '-release-listing.html'

    put_release_html_in_s3_response = s3.put_object(Bucket=release_details['S3_BUCKET_NAME'], Key=destination_key,
                                                    Body=encoded_string,
                                                    ContentType='text/html')
    logger.info(put_release_html_in_s3_response)
    return rendered


def fetch_all_application_releases(s3_bucket, s3_query_prefix):
    """ Retrieve all application releases for a given application and client"""
    s3_release_list = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_query_prefix)
    release_list = []
    for o in s3_release_list['Contents']:
        print(o['Key'])
        if "-release-notes.html" in o['Key']:
            release_dict = {}
            release_dict["ReleaseNotesLink"] = 'https://s3.amazonaws.com/' + s3_bucket + '/' + \
                                               o['Key']
            release_dict["ReleaseVersion"] = o['Key'].split('/')[4].replace("-release-notes.html", "")
            release_type = re.search('(v\d+(?:\.\d+)*)(?:[-]([A-Za-z]+))?((?:\.\d+)*)',
                                     str(release_dict['ReleaseVersion']))
            print(release_type.group(2))
            release_dict["ReleaseTypeCss"] = release_type_css_switcher(release_type.group(2))
            release_dict["ReleaseDate"] = o['LastModified']
            release_list.append(release_dict)

    print(release_list)
    release_list.sort(key=operator.itemgetter('ReleaseDate'), reverse=True)

    return release_list


def release_type_css_switcher(release_type):
    """ Perform Switch functionality to return the correct CSS value based on Release Type"""
    if not release_type:
        release_type = ""

    switcher = {
                "": "success",
                "rc": "info",
                "beta": "warning",
                "hotfix": "danger"
    }

    return switcher.get(release_type, "Invalid Release Type")


def move_release_to_s3_destination(release_details):
    """ Copy file from Polling directory to Permanent Location based on Release Details,
    Delete the file from the polling directory"""
    destination_key = release_details['CLIENT_CODE'] + '/applications/' + release_details['APPLICATION_CODE'] +\
        '/releases/' + release_details['ARCHIVE_NAME']

    delete_source = False
    move_s3_file(release_details['S3_BUCKET_NAME'], release_details['S3_FILE_KEY'],
                 release_details['S3_BUCKET_NAME'], destination_key,
                 delete_source)
    return None


def move_s3_file(s3_current_bucket, s3_current_file_key, s3_new_bucket, s3_new_file_key, delete_source):
    """ Move a file from one location to another in an S3 Bucket"""
    s3_source_details = {'Bucket': s3_current_bucket, 'Key': s3_current_file_key}
    move_s3_destination_response = s3.copy_object(Bucket=s3_new_bucket,
                                                  Key=s3_new_file_key, CopySource=s3_source_details)
    logger.info(move_s3_destination_response)

    if delete_source:
        delete_from_s3_response = s3.delete_object(Bucket=s3_current_bucket,
                                                   Key=s3_current_file_key)
        logger.info(delete_from_s3_response)


def trigger_jenkins(application_release):
    """ Trigger Jenkins Pipeline to execute Packer Image Creation Process"""
    username = os.environ['USERNAME']
    token = os.environ['API_TOKEN']
    encoded_data = urllib.parse.urlencode(application_release)
    parameters = urllib.parse.quote_plus(encoded_data)
    url = '{}/job/PackerImageBuild/buildWithParameters?{}'.format(os.environ['LOAD_BALANCER'], parameters)
    response = requests.post(url, data=application_release, auth=(username, token))

    return response.status_code



