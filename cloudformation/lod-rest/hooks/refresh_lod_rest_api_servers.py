from sceptre.hooks import Hook
from sceptre.stack import Stack
from time import sleep
import boto3


class RefreshLodRestApiServers(Hook):

    def __init__(self, *args, **kwargs):
        super(RefreshLodRestApiServers, self).__init__(*args, **kwargs)

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
        environment, stack = self.argument.split("::")
        print("Environment: " + environment)
        print("Stack: " + stack)

        stack = Stack(name=environment + "/" + stack, environment_config=self.environment_config,
                      connection_manager=self.connection_manager)

        resources = stack.describe_resources()

        if resources:
            rest_api_autoscaling_group_name = [resource['PhysicalResourceId'] for resource in resources if
                                               resource['LogicalResourceId'] == 'RestApiAutoscalingGroup']
            print("AutoScaling-Group to be Refreshed: " + rest_api_autoscaling_group_name[0])

            autoscaling = boto3.client('autoscaling')

            print("Begin refreshing API server instances...")
            sleep(3)

            autoscaling_group_response = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[rest_api_autoscaling_group_name[0]])

            print("--------Begin AutoScaling-Group Describe Resources Response (Pre-Termination)----")
            print(autoscaling_group_response)
            print("--------End AutoScaling-Group Describe Resources Response (Pre-Termination)--------")

            current_instances = autoscaling_group_response['AutoScalingGroups'][0]['Instances']
            for instance in current_instances:
                instance_id = instance['InstanceId']
                print(instance_id)
                ec2 = boto3.client('ec2')
                waiter = ec2.get_waiter('instance_terminated')

                ec2.terminate_instances(InstanceIds=[instance_id])
                print("Instance terminating...")
                waiter.wait(InstanceIds=[instance_id])
                print("Instance successfully terminated!")

            print("All Instances terminated, wait 3 Minutes for AutoScaling-Group Details to refresh...")
            sleep(160)

            autoscaling_group_response = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[rest_api_autoscaling_group_name[0]])

            print("--------Begin AutoScaling-Group Describe Resources Response (Post-Termination)----")
            print(autoscaling_group_response)
            print("--------End AutoScaling-Group Describe Resources Response (Post-Termination)--------")

            asg_desired_capacity = autoscaling_group_response['AutoScalingGroups'][0]['DesiredCapacity']
            in_service_instances = 0
            in_service_current_loop = 0
            print("Begin Polling for new InService Instances...")
            while in_service_instances != asg_desired_capacity:
                print("Pause for 30 seconds between polling events...")
                sleep(30)

                print("Desired Capacity is: " + str(asg_desired_capacity))
                print("InService Instance Count is: " + str(in_service_instances))

                autoscaling_group_response = autoscaling.describe_auto_scaling_groups(
                    AutoScalingGroupNames=[rest_api_autoscaling_group_name[0]])

                current_instances = autoscaling_group_response['AutoScalingGroups'][0]['Instances']

                for instance in current_instances:
                    instance_id = instance['InstanceId']
                    print(instance_id)
                    print("Instance Lifecycle State: " + instance['LifecycleState'])
                    if instance['LifecycleState'] == "InService":
                        in_service_current_loop += 1
                        in_service_instances = in_service_current_loop

                in_service_current_loop = 0

            print("Desired Capacity is: " + str(asg_desired_capacity))
            print("InService Instance Count is: " + str(in_service_instances))
            print("All Instances are InService!")
