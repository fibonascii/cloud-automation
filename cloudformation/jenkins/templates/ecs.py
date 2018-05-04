from base import BaseCloudFormation

class ECSCluster(BaseCloudFormation):
    def __init__(self, sceptre_user_data):
        super().__init__()
        self.add_paramaeters()
        self.add_resources()

    def add_paramaters(self):
         pass

    def add_resources(self):
        ContainerInstances = self.template.add_resource(LaunchConfiguration(
             'ContainerInstances',

             

def sceptre_handler(sceptre_user_data):
    ecs = ECSCluster(sceptre_user_data)
    return ecs.template.to_json()
