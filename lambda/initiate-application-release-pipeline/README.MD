# Initiate Application Release Pipeline

### About

This AWS Lambda function polls an S3 bucket utilizing S3 Event Notifications.
When a REST release zip file is uploaded to this bucket the lambda function unzips the release,
parses metadata from the zip and passes those values to Jenkins as parameters


#### Usage 

The Lambda function requires two policies. 

    {
      "Version": "2012-10-17",
      "Statement": {
       "Effect": "Allow",
       "Principal": {"Service": "lambda.amazonaws.com"},
       "Action": "sts:AssumeRole"
     }
    }


 The above trust policy specifies which trusted account members are allowed to assume the role
 
     {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::*"
        }
       ]
    }

The above permissions role gives S3 The proper access permissions to get and put objects in the corresponding s3 bucket


#### Environment Variables

Several environment  variables have to be set in the AWS Lambda function to work properly

    API_TOKEN: YOUR JENKINS API TOKEN
    LOAD_BALANCER: THE JENKINS ELB THAT LAMBDA WILL CALL
    USERNAME: THE USERNAME TO POST TO JENKINS API
