import json

def get_ami_id():

    build_artifact = "../../jenkins-pipeline/validatebuild/manifest.json"
    with open(build_artifact) as file:
        artifacts = json.load(file)
        ami = artifacts['builds'][0]['artifact_id'].split(':')[1]

    return ami


get_ami_id()
