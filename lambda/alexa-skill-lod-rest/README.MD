# Alexa Skill for Loyalty On Demand Rest

### About

This AWS Lambda function communicates with the Loyalty On Demand Rest Environment to provide interaction back to the user via an Alexa Skill.


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

    CLIENT_DISPLAY_NAME: THE NAME OF THE ALEXA SKILL
    CLIENT_SERVICE_ID: THE REST API CLIENT ID
    CLIENT_SERVICE_SECRET: THE REST API SECRET
    CLIENT_SERVICE_URL: THE REST API URL
    MEMBER_EVENT: THE EVENT THAT ALEXA CAN TRIGGER A BONUS FOR VIA REST API CALL
    MEMBER_ID: THE MEMBER ID OF THE MEMBER WHOM WILL INTERACT WITH THE SKILL (SHOULD BE DEPRECATED ONCE INTEGRATION WITH ALEXA USER FUNCTIONS IS COMPLETE)
    VIRTUAL_ASSISTANCE_EXPERIENCE: THE TITLE OF THE VIRTUAL ASSISTANT (i.e. Virtual Concierge, Virtual Assistant, etc.)
