from base import BaseCloudFormation
from troposphere import ec2, Ref, Tags, Parameter, GetAtt, Output, Base64, Join, elasticloadbalancing
from troposphere.ssm import Parameter as SSMParameter


class DeployRest(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()

        self.add_parameters()
        self.add_resources()
        self.add_outputs()

    def add_parameters(self):
        self.AdminCidrBlock = self.template.add_parameter(Parameter(
            "AdminCidrBlock",
            Type="String",
        ))

        self.OAuthPrivateLoadBalancerDNS = self.template.add_parameter(Parameter(
            "OAuthPrivateLoadBalancerDNS",
            Type="String",
        ))

        self.OAuthPublicLoadBalancerDNS = self.template.add_parameter(Parameter(
            "OAuthPublicLoadBalancerDNS",
            Type="String",
        ))

        self.OAuthPublicLoadBalancerSecurityGroup = self.template.add_parameter(Parameter(
            "OAuthPublicLoadBalancerSecurityGroup",
            Type="String",
        ))

        self.RestApiPrivateLoadBalancerDNS = self.template.add_parameter(Parameter(
            "RestApiPrivateLoadBalancerDNS",
            Type="String",
        ))

        self.RestApiAutoScalingGroupName = self.template.add_parameter(Parameter(
            "RestApiAutoScalingGroupName",
            Type="String",
        ))

        self.EnvironmentArtifactsS3Bucket = self.template.add_parameter(Parameter(
            "EnvironmentArtifactsS3Bucket",
            Type="String",
        ))

        self.OAuthConfigurationFilesLocation = self.template.add_parameter(Parameter(
            "OAuthConfigurationFilesLocation",
            Type="String",
        ))

        self.RestApiPrefix = self.template.add_parameter(Parameter(
            "RestApiPrefix",
            Type="String",
        ))

        self.OAuthAdminPort = self.template.add_parameter(Parameter(
            "OAuthAdminPort",
            Type="String",
        ))

        self.OAuthRestApiProvisionKey = self.template.add_parameter(Parameter(
            "OAuthRestApiProvisionKey",
            Type="String",
        ))

        self.OAuthRestApiKongConsumerClientId = self.template.add_parameter(Parameter(
            "OAuthRestApiKongConsumerClientId",
            Type="String",
        ))

        self.OAuthRestApiKongConsumerClientSecret = self.template.add_parameter(Parameter(
            "OAuthRestApiKongConsumerClientSecret",
            Type="String",
        ))

        self.LoyaltyOnDemandOrganization = self.template.add_parameter(Parameter(
            "LoyaltyOnDemandOrganization",
            Type="String",
        ))

        self.LoyaltyOnDemandEnvironment = self.template.add_parameter(Parameter(
            "LoyaltyOnDemandEnvironment",
            Type="String",
        ))


    def add_resources(self):
        self.RestApiPrefixSSMParameter = self.template.add_resource(SSMParameter(
            "RestApiPrefixSSMParameter",
            Description="The Rest API Prefix",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-restApiPrefix",
            Type="String",
            Value=Ref(self.RestApiPrefix),
        ))

        self.OAuthInternalLoadBalancerSSMParameter = self.template.add_resource(SSMParameter(
            "OAuthInternalLoadBalancerParameter",
            Description="The OAuth Internal Load Balancer",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-restKongEndpoint",
            Type="String",
            Value=Ref(self.OAuthPrivateLoadBalancerDNS),
        ))

        self.OAuthRestApiProvisionKeySSMParameter = self.template.add_resource(SSMParameter(
            "OAuthProvisionKeySSMParameter",
            Description="The OAuth Rest Api Provision Key",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-restKongProvisionKey",
            Type="String",
            Value=Ref(self.OAuthRestApiProvisionKey),
        ))

        self.OAuthRestApiKongConsumerClientIdSSMParameter = self.template.add_resource(SSMParameter(
            "OAuthRestApiKongConsumerClientIdSSMParameter",
            Description="The OAuth Rest Api Kong Consumer Client Id Key",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-restKongConsumerClientId",
            Type="String",
            Value=Ref(self.OAuthRestApiKongConsumerClientId),
        ))

        self.OAuthRestApiKongConsumerClientSecretSSMParameter = self.template.add_resource(SSMParameter(
            "OAuthRestApiKongConsumerClientSecretSSMParameter",
            Description="The OAuth Rest Api Kong Consumer Client Secret Key",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-restKongConsumerClientSecret",
            Type="String",
            Value=Ref(self.OAuthRestApiKongConsumerClientSecret),
        ))

        self.LoyaltyOnDemandOrganizationSSMParameter = self.template.add_resource(SSMParameter(
            "LoyaltyOnDemandOrganizationSSMParameter",
            Description="The Loyalty On Demand Organization",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-loyaltyWareOrganization",
            Type="String",
            Value=Ref(self.LoyaltyOnDemandOrganization),
        ))

        self.LoyaltyOnDemandEnvironmentSSMParameter = self.template.add_resource(SSMParameter(
            "LoyaltyOnDemandEnvironmentSSMParameter",
            Description="The Loyalty On Demand Environment",
            Name=self.environment_parameters["ClientEnvironmentKey"] + "-loyaltyWareEnvironment",
            Type="String",
            Value=Ref(self.LoyaltyOnDemandEnvironment),
        ))

    def add_outputs(self):
        self.template.add_output(Output(
            "OAuthRestApiProvisionKeySSMParameter",
            Value=GetAtt(self.OAuthRestApiProvisionKeySSMParameter, "Value"),
        ))

        self.template.add_output(Output(
            "OAuthRestApiKongConsumerClientIdSSMParameter",
            Value=GetAtt(self.OAuthRestApiKongConsumerClientIdSSMParameter, "Value"),
        ))

        self.template.add_output(Output(
            "OAuthRestApiKongConsumerClientSecretSSMParameter",
            Value=GetAtt(self.OAuthRestApiKongConsumerClientSecretSSMParameter, "Value"),
        ))

        self.template.add_output(Output(
            "LoyaltyOnDemandOrganizationSSMParameter",
            Value=GetAtt(self.LoyaltyOnDemandOrganizationSSMParameter, "Value"),
        ))

        self.template.add_output(Output(
            "LoyaltyOnDemandEnvironmentSSMParameter",
            Value=GetAtt(self.LoyaltyOnDemandEnvironmentSSMParameter, "Value"),
        ))

def sceptre_handler(sceptre_user_data):
    restapi = DeployRest(sceptre_user_data)
    return restapi.template.to_json()
