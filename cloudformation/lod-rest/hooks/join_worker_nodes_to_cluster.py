from sceptre.hooks import Hook
from sceptre.stack import Stack
import yaml
import os
from os import path
from jinja2 import Environment, FileSystemLoader
from time import sleep
import boto3
import json


class JoinWorkerNodesToCluster(Hook):

    def __init__(self, *args, **kwargs):
        super(JoinWorkerNodesToCluster, self).__init__(*args, **kwargs)

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
        environment = self.environment_config.environment_path + "/" + self.stack_config.name

        stack = Stack(name=environment, environment_config=self.environment_config,
                      connection_manager=self.connection_manager)

        outputs = stack.describe_outputs()
        print(outputs)

        if outputs:
            eks_cluster_name = [output['OutputValue'] for output in outputs if
                                       output['OutputKey'] == 'EKSClusterName']
            print(eks_cluster_name[0])

            connect_to_cluster_cmd = "aws eks update-kubeconfig --name {}".format(eks_cluster_name[0])
            os.system(connect_to_cluster_cmd)

            worker_node_instance_role_arn = [output['OutputValue'] for output in outputs if
                                             output['OutputKey'] == 'WorkerNodeInstanceRoleArn']
            print(worker_node_instance_role_arn[0])

            basepath = path.dirname(__file__)
            print(basepath)
            config_map_yaml_path = path.abspath(path.join(basepath, "ss_eks_config_map.yaml"))
            print(config_map_yaml_path)

            basepath = path.dirname(__file__)
            print(basepath)
            config_map_template_path = path.abspath(path.join(basepath, "ss_eks_config_map.j2.template"))
            print(config_map_template_path)

            j2_env = Environment(loader=FileSystemLoader(basepath), trim_blocks=True)
            template = j2_env.get_template("ss_eks_config_map.j2.template")
            render_values = {"role_arn": worker_node_instance_role_arn[0], "EC2PrivateDNSName": "{{EC2PrivateDNSName}}"}
            rendered = template.render(render_values)

            with open('hooks/ss_eks_config_map.yaml', 'w') as f:
                f.write(rendered)

            connect_worker_nodes_to_cluster_cmd = "kubectl apply -f {}".format(config_map_yaml_path)
            os.system(connect_worker_nodes_to_cluster_cmd)

            worker_node_autoscaling_group_name = [output['OutputValue'] for output in outputs if
                                             output['OutputKey'] == 'WorkerNodeAutoScalingGroupName']
            print(worker_node_autoscaling_group_name[0])

            autoscaling = boto3.client('autoscaling')
            autoscaling_group_response = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[worker_node_autoscaling_group_name[0]])

            asg_desired_capacity = autoscaling_group_response['AutoScalingGroups'][0]['DesiredCapacity']
            ready_nodes = 0
            ready_nodes_current_loop = 0
            print(asg_desired_capacity)

            print("Begin Polling for new Ready Worker Nodes...")
            while ready_nodes != asg_desired_capacity:
                print("Pause for 30 seconds between polling events...")
                sleep(5)

                print("Desired Capacity is: " + str(asg_desired_capacity))
                print("Ready Worker Node Count is: " + str(ready_nodes))

                get_node_status_cmd = "kubectl get nodes -o json"
                current_nodes_status = os.popen(get_node_status_cmd).read()
                current_nodes_status_json = json.loads(current_nodes_status)
                nodes = current_nodes_status_json['items']

                for node in nodes:
                    node_conditions = node['status']['conditions']
                    print(node_conditions)
                    for condition in node_conditions:
                        if condition['reason'] == 'KubeletReady':
                            if condition['type'] == 'Ready' and condition['status'] == 'True':
                                ready_nodes_current_loop += 1
                                ready_nodes = ready_nodes_current_loop

                ready_nodes_current_loop = 0

            print("Desired Capacity is: " + str(asg_desired_capacity))
            print("Ready Worker Node Count is: " + str(ready_nodes))
            print("All Worker Nodes are Ready!")


