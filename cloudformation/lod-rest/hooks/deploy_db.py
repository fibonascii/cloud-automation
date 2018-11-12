from sceptre.hooks import Hook
from sceptre.stack import Stack
import yaml
import os
import shutil
from os import path
from jinja2 import Environment, FileSystemLoader
from time import sleep
import boto3
import json


class DeployDb(Hook):

    def __init__(self, *args, **kwargs):
        super(DeployDb, self).__init__(*args, **kwargs)

    def handle_temporary_access(self, client, action, security_group_id, source_security_group_id):
        # Create Ingress Rule to allow traffic to kong
        if action == "authorize":
            print("Opening Temporary Access")
            response = client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{"IpProtocol": "tcp", "FromPort": 1521, "ToPort": 1521,
                                "UserIdGroupPairs": [{'GroupId': source_security_group_id}]}]
            )

            print(response)

        if action == "revoke":
            print("Removing Temporary Access")
            response = client.revoke_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{"IpProtocol": "tcp", "FromPort": 1521, "ToPort": 1521,
                                "UserIdGroupPairs": [{'GroupId': source_security_group_id}]}]
            )

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
        environment = self.environment_config.environment_path + "/" + self.stack_config.name

        database_stack = Stack(name=environment, environment_config=self.environment_config,
                      connection_manager=self.connection_manager)

        database_outputs = database_stack.describe_outputs()
        print("Database Outputs")
        print(database_outputs)

        eks_stack = Stack(name=self.environment_config.environment_path + "/sseks",
                           environment_config=self.environment_config,
                           connection_manager=self.connection_manager)

        eks_outputs = eks_stack.describe_outputs()
        print("Shared EKS Outputs")
        print(eks_outputs)

        vpc_stack = Stack(name=self.environment_config.environment_path + "/vpc",
                          environment_config=self.environment_config,
                          connection_manager=self.connection_manager)

        print("Client VPC Outputs")
        vpc_outputs = vpc_stack.describe_outputs()
        print(vpc_outputs)

        if database_outputs:
            eks_cluster_name = [output['OutputValue'] for output in eks_outputs if
                                       output['OutputKey'] == 'EKSClusterName']
            print(eks_cluster_name[0])

            connect_to_cluster_cmd = "aws eks update-kubeconfig --name {}".format(eks_cluster_name[0])
            os.system(connect_to_cluster_cmd)

            eks_worker_node_sg = [output['OutputValue'] for output in eks_outputs if
                                             output['OutputKey'] == 'WorkerNodeEc2SG']
            print(eks_worker_node_sg[0])

            db_sg = [output['OutputValue'] for output in database_outputs if
                                  output['OutputKey'] == 'OracleRestDBSecurityGroup']
            print(db_sg[0])

            vpc_id = [output['OutputValue'] for output in vpc_outputs if
                      output['OutputKey'] == 'VpcId']
            print(vpc_id[0])

            client_artifacts_s3_bucket = [output['OutputValue'] for output in vpc_outputs if
                                          output['OutputKey'] == 'EnvironmentArtifactsS3Bucket']
            print(client_artifacts_s3_bucket[0])

            core_artifacts_s3_bucket = [output['OutputValue'] for output in vpc_outputs if
                                          output['OutputKey'] == 'CoreBootStrapRepositoryS3BucketName']
            print(core_artifacts_s3_bucket[0])

            # Instance Identifier
            database_desc = database_stack.describe()

            db_name = [parameter['ParameterValue'] for parameter in
                                                database_desc['Stacks'][0]['Parameters'] if
                                                parameter['ParameterKey'] == 'OracleRestDBName']
            print(db_name[0])

            # Admin Name
            admin_username = [parameter['ParameterValue'] for parameter in
                                                database_desc['Stacks'][0]['Parameters'] if
                                                parameter['ParameterKey'] == 'OracleRestDBUsername']
            print(admin_username[0])

            # Admin Password
            admin_password = [parameter['ParameterValue'] for parameter in
                                                database_desc['Stacks'][0]['Parameters'] if
                                                parameter['ParameterKey'] == 'OracleRestDBPassword']
            print(admin_password[0])

            db_base_framework_s3_key = [parameter['ParameterValue'] for parameter in
                              database_desc['Stacks'][0]['Parameters'] if
                              parameter['ParameterKey'] == 'DatabaseBaseFrameworkScriptsLocation']
            print(db_base_framework_s3_key[0])

            db_release_framework_s3_key = [parameter['ParameterValue'] for parameter in
                                           database_desc['Stacks'][0]['Parameters'] if
                                           parameter['ParameterKey'] == 'DatabaseReleaseFrameworkScriptsLocation']
            print(db_release_framework_s3_key[0])

            basepath = path.dirname(__file__)
            print(basepath)
            scripts_dir = basepath + "/temp/scripts/"
            print(scripts_dir)
            os.makedirs(scripts_dir, exist_ok=True)
            schema_dir = basepath + "/temp/lf-schema/"
            print(schema_dir)
            os.makedirs(schema_dir, exist_ok=True)
            object_dir = basepath + "/temp/lf-objects/"
            print(object_dir)
            os.makedirs(object_dir, exist_ok=True)
            perf_dir = basepath + "/temp/performance-tuning/"
            print(perf_dir)
            os.makedirs(perf_dir, exist_ok=True)
            configmap_dir = basepath + "/temp/config-maps/"
            print(configmap_dir)
            os.makedirs(configmap_dir, exist_ok=True)

            # open and close security group of DB from shared cluster
            ec2 = boto3.client('ec2')
            self.handle_temporary_access(ec2, "authorize", db_sg[0],
                                         eks_worker_node_sg[0])



            # Pull LF Scripts from release S3
            s3 = boto3.resource('s3')

            print("Downloading scripts from Client Environment S3")
            framework_core_scripts = db_base_framework_s3_key[0] + "bash-scripts/"
            download_bucket = s3.Bucket(client_artifacts_s3_bucket[0])
            for s3_object in download_bucket.objects.filter(Prefix=framework_core_scripts):
                if s3_object.key[-1] == "/":
                    continue
                download_key = s3_object.key
                local_scripts_path = download_key.replace(framework_core_scripts, 'hooks/temp/scripts/')
                print(download_key)
                print("Local Scripts Path")
                print(local_scripts_path)
                s3.Bucket(client_artifacts_s3_bucket[0]).download_file(download_key, local_scripts_path)

            framework_core_db_schema_scripts = db_base_framework_s3_key[0] + "db-scripts/schema/"
            download_bucket = s3.Bucket(client_artifacts_s3_bucket[0])
            for s3_object in download_bucket.objects.filter(Prefix=framework_core_db_schema_scripts):
                if s3_object.key[-1] == "/":
                    continue
                download_key = s3_object.key
                local_db_schema_scripts_path = download_key.replace(framework_core_db_schema_scripts, 'hooks/temp/lf-schema/')
                print(download_key)
                print("Local Schema Scripts Path")
                print(local_db_schema_scripts_path)
                s3.Bucket(client_artifacts_s3_bucket[0]).download_file(download_key, local_db_schema_scripts_path)

            framework_core_db_perf_scripts = db_base_framework_s3_key[0] + "db-scripts/performance-tuning/"
            download_bucket = s3.Bucket(client_artifacts_s3_bucket[0])
            for s3_object in download_bucket.objects.filter(Prefix=framework_core_db_perf_scripts):
                if s3_object.key[-1] == "/":
                    continue
                download_key = s3_object.key
                local_db_perf_scripts_path = download_key.replace(framework_core_db_perf_scripts, 'hooks/temp/performance-tuning/')
                print(download_key)
                print("Local DB Perf Path")
                print(local_db_perf_scripts_path)
                s3.Bucket(client_artifacts_s3_bucket[0]).download_file(download_key, local_db_perf_scripts_path)

                framework_release_db_lf_scripts = db_release_framework_s3_key[0]
                download_bucket = s3.Bucket(core_artifacts_s3_bucket[0])
                for s3_object in download_bucket.objects.filter(Prefix=framework_release_db_lf_scripts):
                    if s3_object.key[-1] == "/":
                        continue
                    download_key = s3_object.key
                    local_release_db_lf_scripts_path = download_key.replace(framework_release_db_lf_scripts,
                                                                      'hooks/temp/lf-objects/')
                    print(download_key)
                    print("Local LF Objects Path")
                    print(local_release_db_lf_scripts_path)
                    s3.Bucket(core_artifacts_s3_bucket[0]).download_file(download_key, local_release_db_lf_scripts_path)

            # Pull Execution Scripts from client S3 (must store there first in VPC Stack)

            # template out DB_Info.yaml
            print("Render DB Info YAML")
            db_endpoint = db_name[0] + ".c3q1lm3catiz.us-east-1.rds.amazonaws.com"
            db_info_yaml_path = path.abspath(
                path.join(basepath, "db_info.yaml"))
            print(db_info_yaml_path)

            db_info_template_path = path.abspath(path.join(basepath, "db_info.j2.template"))
            print(db_info_template_path)

            j2_env = Environment(loader=FileSystemLoader(basepath), trim_blocks=True)
            template = j2_env.get_template("db_info.j2.template")
            render_values = {"db_admin_username": admin_username[0], "db_admin_password": admin_password[0], "db_endpoint": db_endpoint, "db_name": db_name[0]}
            rendered = template.render(render_values)

            with open('hooks/temp/scripts/db_info.yaml', 'w') as f:
                f.write(rendered)
            print("DB Info YAML Rendered!")

            # Create Client Namespace
            print("Create Client VPC Namespace in Shared EKS Cluster")
            client_vpc_cluster_namespace = vpc_id[0] + "-" + self.environment_config.environment_path
            client_vpc_cluster_namespace_yaml_path = path.abspath(path.join(basepath, "client_vpc_cluster_namespace.yaml"))
            print(client_vpc_cluster_namespace_yaml_path)

            config_map_template_path = path.abspath(path.join(basepath, "client_vpc_cluster_namespace.j2.template"))
            print(config_map_template_path)

            j2_env = Environment(loader=FileSystemLoader(basepath), trim_blocks=True)
            template = j2_env.get_template("client_vpc_cluster_namespace.j2.template")
            render_values = {"client_namespace": client_vpc_cluster_namespace}
            rendered = template.render(render_values)

            with open('hooks/client_vpc_cluster_namespace.yaml', 'w') as f:
                f.write(rendered)

            create_client_vpc_cluster_namespace_cmd = "kubectl apply -f {}".format(client_vpc_cluster_namespace_yaml_path)
            os.system(create_client_vpc_cluster_namespace_cmd)
            print("Client VPC Namespace created in Shared EKS Cluster!")

            # Create Config Maps
            print("Create Schema Config Map")

            create_schema_configmap_yaml_cmd = "kubectl create configmap --dry-run lf-schema " \
                                                      "--from-file={} --namespace={} " \
                                                      "--output yaml | tee {}lf-schema-configmap.yaml".format(schema_dir, client_vpc_cluster_namespace,configmap_dir)
            os.system(create_schema_configmap_yaml_cmd)

            schema_configmap_yaml_path = "{}lf-schema-configmap.yaml".format(configmap_dir)
            print(schema_configmap_yaml_path)

            create_schema_configmap_cmd = "kubectl apply -f {}".format(schema_configmap_yaml_path)
            os.system(create_schema_configmap_cmd)
            print("Schema Config Map Created!")

            print("Create LoyaltyFramework Objects Config Map")

            create_lf_objects_configmap_yaml_cmd = "kubectl create configmap --dry-run lf-oracle-objects " \
                                               "--from-file={} --namespace={} " \
                                               "--output yaml | tee {}lf-oracle-objects.yaml".format(object_dir,
                                                                                                       client_vpc_cluster_namespace,
                                                                                                       configmap_dir)
            os.system(create_lf_objects_configmap_yaml_cmd)

            lf_objects_configmap_yaml_path = "{}lf-oracle-objects.yaml".format(configmap_dir)
            print(lf_objects_configmap_yaml_path)

            create_lf_objects_configmap_cmd = "kubectl apply -f {}".format(lf_objects_configmap_yaml_path)
            os.system(create_lf_objects_configmap_cmd)
            print("LF Objects Config Map Created!")

            print("Create Performance Tuning Config Map")

            create_perf_configmap_yaml_cmd = "kubectl create configmap --dry-run perf-tuning " \
                                               "--from-file={} --namespace={} " \
                                               "--output yaml | tee {}perf-tuning-configmap.yaml".format(perf_dir,
                                                                                                       client_vpc_cluster_namespace,
                                                                                                       configmap_dir)
            os.system(create_perf_configmap_yaml_cmd)

            perf_configmap_yaml_path = "{}perf-tuning-configmap.yaml".format(configmap_dir)
            print(schema_configmap_yaml_path)

            create_perf_configmap_cmd = "kubectl apply -f {}".format(perf_configmap_yaml_path)
            os.system(create_perf_configmap_cmd)
            print("Performance Tuning Config Map Created!")

            print("Create Execution Scripts Config Map")

            create_exec_scripts_configmap_yaml_cmd = "kubectl create configmap --dry-run execution-scripts " \
                                             "--from-file={} --namespace={} " \
                                             "--output yaml | tee {}execution-scripts-configmap.yaml".format(scripts_dir,
                                                                                                       client_vpc_cluster_namespace,
                                                                                                       configmap_dir)
            os.system(create_exec_scripts_configmap_yaml_cmd)

            exec_scripts_configmap_yaml_path = "{}execution-scripts-configmap.yaml".format(configmap_dir)
            print(exec_scripts_configmap_yaml_path)

            create_exec_scripts_configmap_cmd = "kubectl apply -f {}".format(exec_scripts_configmap_yaml_path)
            os.system(create_exec_scripts_configmap_cmd)
            print("Execution Scripts Config Map Created!")

            # Create Job
            print("Create Oracle Deployment Job")
            db_ora_deploy_job_name = "deploy-ora-{}".format(client_vpc_cluster_namespace)
            db_ora_deploy_yaml_path = path.abspath(
                path.join(basepath, "deploy-lf-oracle-job.yaml"))
            print(db_ora_deploy_yaml_path)

            db_ora_deploy_job_template_path = path.abspath(path.join(basepath, "deploy-lf-oracle-job.j2.template"))
            print(db_ora_deploy_job_template_path)

            j2_env = Environment(loader=FileSystemLoader(basepath), trim_blocks=True)
            template = j2_env.get_template("deploy-lf-oracle-job.j2.template")
            render_values = {"db_ora_deploy_job_name": db_ora_deploy_job_name, "client_namespace": client_vpc_cluster_namespace}
            rendered = template.render(render_values)

            with open('hooks/deploy-lf-oracle-job.yaml', 'w') as f:
                f.write(rendered)

                db_ora_deploy_cmd = "kubectl apply -f {}".format(
                db_ora_deploy_yaml_path)
            os.system(db_ora_deploy_cmd)
            print("Oracle Deployment Job Created!")


            # Monitor Execution for success

            # Delete temp folder
            shutil.rmtree(basepath + "/temp/")

            # Remove Temporary DB Access
            sleep(30)
            self.handle_temporary_access(ec2, "revoke", db_sg[0],
                                         eks_worker_node_sg[0])








