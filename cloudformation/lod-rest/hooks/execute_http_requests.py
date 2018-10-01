from sceptre.hooks import Hook
from sceptre.stack import Stack
from sceptre.environment import Environment
from botocore.vendored import requests
import boto3
import json
# Newman Params
import os
from os import path


class ExecuteHttpRequests(Hook):

    def __init__(self, *args, **kwargs):
        super(ExecuteHttpRequests, self).__init__(*args, **kwargs)

    def handle_temporary_access(self, client, action, security_group_id, cidr_block):
        # Create Ingress Rule to allow traffic to kong
        if action == "authorize":
            print("Opening Temporary Access")
            response = client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpProtocol="tcp",
                CidrIp=cidr_block,
                FromPort=9100,
                ToPort=9200)

            print(response)

        if action == "revoke":
            print("Removing Temporary Access")
            response = client.revoke_security_group_ingress(
                GroupId=security_group_id,
                IpProtocol="tcp",
                FromPort=9100,
                ToPort=9200,
                CidrIp=cidr_block)

            print(response)

        return None

    def run(self):
        """
        run is the method called by Sceptre. It should carry out the work
        intended by this hook.

        self.argument is available from the base class and contains the
        argument defined in the sceptre config file (see below)

        The following attributes may be available from the base class:
        self.stack_config  (A dict of data from <stack_name>.yaml)
        self.environment_config  (A dict of data from config.yaml)
        self.connection_manager (A connection_manager)
        """
        action = self.argument
        print(action)
        print(self.stack_config)

        environment = self.environment_config.environment_path + "/" + self.stack_config.name

        kong_stack = Stack(name=self.environment_config.environment_path + "/kong", environment_config=self.environment_config,
                      connection_manager=self.connection_manager)

        kong_outputs = kong_stack.describe_outputs()
        print(kong_outputs)

        restapi_stack = Stack(name=self.environment_config.environment_path + "/restapi",
                           environment_config=self.environment_config,
                           connection_manager=self.connection_manager)

        restapi_outputs = restapi_stack.describe_outputs()
        print(restapi_outputs)

        vpc_stack = Stack(name=self.environment_config.environment_path + "/vpc",
                              environment_config=self.environment_config,
                              connection_manager=self.connection_manager)

        vpc_outputs = vpc_stack.describe_outputs()
        print(vpc_outputs)
        exit

        if restapi_outputs:

            admin_cidr_block = [output['OutputValue'] for output in vpc_outputs if
                                       output['OutputKey'] == 'AdminCidrBlock']
            print(admin_cidr_block[0])

            local_public_ip = requests.get('http://ip.42.pl/raw').text
            local_public_ip = local_public_ip + "/32"
            print(local_public_ip)
            print(admin_cidr_block[0])
            temporary_access = local_public_ip != admin_cidr_block[0]
            ec2 = boto3.client('ec2')

            # Call kong API requests
            if action == "configure":

                kong_public_load_balancer_security_group_id = [output['OutputValue'] for output in kong_outputs if
                                                               output['OutputKey'] == 'KongPublicLoadBalancerSecurityGroup']
                print(kong_public_load_balancer_security_group_id[0])

                if temporary_access:
                    self.handle_temporary_access(ec2,"authorize", kong_public_load_balancer_security_group_id[0],
                                                 local_public_ip)

                kong_public_load_balancer_dns = [output['OutputValue'] for output in kong_outputs if
                                                 output['OutputKey'] == 'KongPublicLoadBalancerDNS']
                print(kong_public_load_balancer_dns[0])

                restapi_private_load_balancer_dns = [output['OutputValue'] for output in restapi_outputs if
                                                     output['OutputKey'] == 'RestApiPrivateLoadBalancerDNS']
                print(restapi_private_load_balancer_dns[0])

                env_artifacts_s3_bucket = [output['OutputValue'] for output in vpc_outputs if
                                           output['OutputKey'] == 'EnvironmentArtifactsS3Bucket']
                print(env_artifacts_s3_bucket[0])

                restapi_prefix = self.stack_config['parameters']['RestApiPrefix']
                print(restapi_prefix)

                oauth_admin_port = self.stack_config['parameters']['OAuthAdminPort']
                print(oauth_admin_port)

                postman_files_s3_key = self.stack_config['parameters']['OAuthConfigurationFilesLocation']
                print(postman_files_s3_key)

                # Download Kong Postman Files
                s3 = boto3.resource('s3')

                download_bucket = s3.Bucket(env_artifacts_s3_bucket[0])

                for s3_object in download_bucket.objects.filter(Prefix=postman_files_s3_key):
                    if s3_object.key[-1] == "/":
                        continue
                    download_key = s3_object.key
                    local_postman_path = download_key.replace(postman_files_s3_key, 'hooks/')
                    print(download_key)
                    print(local_postman_path)
                    s3.Bucket(env_artifacts_s3_bucket[0]).download_file(download_key, local_postman_path)

                # Update Kong Postman Environment File
                with open('hooks/kong.postman_environment.json', 'r') as f:
                    json_data = json.load(f)
                    for value in json_data['values']:
                        if value['key'] == "konghost":
                            value['value'] = kong_public_load_balancer_dns[0]

                        if value['key'] == 'upstreamhost':
                            value['value'] = restapi_private_load_balancer_dns[0]

                        if value['key'] == 'adminport':
                            value['value'] = oauth_admin_port

                        if value['key'] == 'apiprefix':
                            value['value'] = restapi_prefix


                with open('hooks/kong.postman_environment.json', 'w') as f:
                    f.write(json.dumps(json_data))

                # Execute Postman via Newman
                basepath = path.dirname(__file__)
                print(basepath)
                postman_collection_path = path.abspath(path.join(basepath, "kong.postman_collection.json"))
                print(postman_collection_path)

                postman_environment_path = path.abspath(path.join(basepath, "kong.postman_environment.json"))
                print(postman_environment_path)

                postman_response_json_path = path.abspath(path.join(basepath, "postman_response.json"))
                print(postman_response_json_path)

                cmd="newman run {0} -e {1} --insecure -r cli,json --reporter-json-export {2}".format(postman_collection_path, postman_environment_path,postman_response_json_path)
                print(os.system(cmd))

                # Parse Postman Response
                with open(postman_response_json_path) as f:
                    postman_response_json_data = json.load(f)

                postman_executions = postman_response_json_data['run']['executions']

                postman_get_consumer_response = [item['assertions'][0]['assertion'] for item in
                                                 postman_executions if
                                                 item['item']['name'] == 'Get Kong Consumer Info']

                postman_get_consumer_response_json = json.loads(postman_get_consumer_response[0])
                self.stack_config['parameters']['OAuthRestApiKongConsumerClientId'] = \
                    postman_get_consumer_response_json['data'][0]['client_id']

                print(self.stack_config['parameters']['OAuthRestApiKongConsumerClientId'])

                self.stack_config['parameters']['OAuthRestApiKongConsumerClientSecret'] = \
                    postman_get_consumer_response_json['data'][0]['client_secret']

                print(self.stack_config['parameters']['OAuthRestApiKongConsumerClientSecret'])

                postman_get_oauth_info_response = [item['assertions'][0]['assertion'] for item in
                                                   postman_executions if
                                                   item['item']['name'] == 'Get OAuth2 Info']

                postman_get_oauth_info_response_json = json.loads(postman_get_oauth_info_response[0])

                self.stack_config['parameters']['OAuthRestApiProvisionKey'] = \
                    postman_get_oauth_info_response_json['data'][0]['config']['provision_key']

                print(self.stack_config['parameters']['OAuthRestApiProvisionKey'])


                if temporary_access:
                    self.handle_temporary_access(ec2, "revoke", kong_public_load_balancer_security_group_id[0],
                                                 local_public_ip)
