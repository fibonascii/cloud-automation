from troposphere import Template, Tags 
from abc import ABC, abstractmethod


class BaseCloudFormation(ABC):
    def __init__(self):
        self.template = Template()
        self.default_tags = Tags(
                  ResourceOwner="ProductDevelopment",
                  Environment="Production",
                  Developer="Reagan Kirby",
                  )
        self.environment_name = "R1KIRB-JENKINS"
   
    @abstractmethod
    def add_parameters(self):
        return

    @abstractmethod
    def add_resources(self):
        return

    @abstractmethod
    def add_outputs(self):
        return
