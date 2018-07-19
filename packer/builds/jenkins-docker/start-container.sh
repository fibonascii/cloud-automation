#!/bin/bash

AWS_ACCESS_KEY_ID=$(aws --profile default configure get aws_access_key_id)
AWS_SECRET_ACCESS_KEY=$(aws --profile default configure get aws_secret_access_key)

docker run -p 8080:8080 --name=jenkins-master -d 844895670466.dkr.ecr.us-east-1.amazonaws.com/jenkins-images:provisioned-master-latest -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY 

