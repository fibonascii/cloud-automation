from troposphere import Template, Tags
from troposphere.autoscaling import Tag as AutoScalingTag
from troposphere.autoscaling import Tags as AutoScalingTags
from abc import ABC, abstractmethod


class BaseCloudFormation(ABC):
    def __init__(self):
        self.template = Template()
        self.base_tags = Tags(
                  ResourceOwner="ProductDevelopment",
                  Environment="Performance",
                  Developer="Jenkins",
                  )

        # self.base_asg_tags = AutoScalingTags(AutoScalingTag("ResourceOwner", "ProductDevelopment", True),
        #                        AutoScalingTag("Environment", "Production", True),
        #                        AutoScalingTag("Developer", "DPreb", True))

        self.environment_parameters = {"EnvironmentName": "Performance",
                                       "ClientCode": "LODPF",
                                       "ClientEnvironmentKey": "D1LODPF",
                                       "EnvironmentRegion": "us-east-1",
                                       "ResourceOwner": "ProductDevelopment"}
   
    @abstractmethod
    def add_parameters(self):
        return

    @abstractmethod
    def add_resources(self):
        return

    @abstractmethod
    def add_outputs(self):
        return
