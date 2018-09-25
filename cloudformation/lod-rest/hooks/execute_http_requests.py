from sceptre.hooks import Hook
from sceptre.stack import Stack
from botocore.vendored import requests
import boto3
import json


class ExecuteHttpRequests(Hook):

    def __init__(self, *args, **kwargs):
        super(ExecuteHttpRequests, self).__init__(*args, **kwargs)

    # def handle_temporary_access(self, client, action, security_group_id, cidr_block):
    #     # Create Ingress Rule to allow traffic to kong
    #     if action == "authorize":
    #         print("Opening Temporary Access")
    #         response = client.authorize_security_group_ingress(
    #             GroupId=security_group_id,
    #             IpProtocol="tcp",
    #             CidrIp=cidr_block,
    #             FromPort=9100,
    #             ToPort=9200)
    #
    #         print(response)
    #
    #     if action == "revoke":
    #         print("Removing Temporary Access")
    #         response = client.revoke_security_group_ingress(
    #             GroupId=security_group_id,
    #             IpProtocol="tcp",
    #             FromPort=9100,
    #             ToPort=9200,
    #             CidrIp=cidr_block)
    #
    #         print(response)
    #
    #     return None

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
        environment, action = self.argument.split("::")
        print(environment)
        print(action)
        stack = Stack(name=environment, environment_config=self.environment_config,
                      connection_manager=self.connection_manager)

        outputs = stack.describe_outputs()
        description = stack.describe()

        admin_cidr_block = [parameter['ParameterValue'] for parameter in description['Stacks'][0]['Parameters'] if
                            parameter['ParameterKey'] == 'AdminCidrBlock']
        print(admin_cidr_block)

        print(outputs)
        if outputs:
            local_public_ip = requests.get('http://ip.42.pl/raw').text
            local_public_ip = local_public_ip + "/32"
            print(local_public_ip)
            print(admin_cidr_block[0])
            temporary_access = local_public_ip != admin_cidr_block[0]
            ec2 = boto3.client('ec2')



                # Call kong API requests
            if action == "configure":
                # Retrieve necessary stack outputs to execute Kong Configuration
                kong_public_load_balancer_security_group_id = [output['OutputValue'] for output in outputs if
                                                               output[
                                                                   'OutputKey'] == 'KongPublicLoadBalancerSecurityGroup']
                print(kong_public_load_balancer_security_group_id[0])

                kong_public_load_balancer_dns = [output['OutputValue'] for output in outputs if
                                                 output['OutputKey'] == 'KongPublicLoadBalancerDNS']
                print(kong_public_load_balancer_dns[0])

                #if temporary_access:
                    # handle_temporary_access(self, ec2,"authorize",kong_public_load_balancer_security_group_id[0],
                                            #local_public_ip)


                #if temporary_access:
                    # handle_temporary_access(self, ec2, "revoke", kong_public_load_balancer_security_group_id[0],
                                            #local_public_ip)
                print("I'm configuring Kong")

            if action == "retrieve-configuration":
                print("I'm using Kong")

        self.stack_config['parameters']['OAuthRestApiProvisionKeySSMParameterValue'] = "33-44"
        self.stack_config['parameters']['OAuthRestApiKongConsumerClientId'] = "555"
        self.stack_config['parameters']['OAuthRestApiKongConsumerClientSecret'] = "777"
