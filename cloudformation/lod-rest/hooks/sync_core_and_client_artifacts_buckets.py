from sceptre.hooks import Hook
from sceptre.stack import Stack
import boto3


class SyncCoreAndClientArtifactsBuckets(Hook):

    def __init__(self, *args, **kwargs):
        super(SyncCoreAndClientArtifactsBuckets, self).__init__(*args, **kwargs)

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
        stack = Stack(name=self.argument, environment_config=self.environment_config,
                      connection_manager=self.connection_manager)

        outputs = stack.describe_outputs()
        if outputs:
            core_artifacts_s3_bucket = self.stack_config['parameters']['CoreBootStrapRepositoryS3BucketName']
            print(core_artifacts_s3_bucket)

            client_artifacts_s3_bucket = [output['OutputValue'] for output in outputs if
                                          output['OutputKey'] == 'EnvironmentArtifactsS3Bucket']
            print(client_artifacts_s3_bucket[0])

            bootstrap_artifacts_key = "bootstrap/"

            s3 = boto3.resource('s3')

            source_bucket = s3.Bucket(core_artifacts_s3_bucket)
            destination_bucket = s3.Bucket(client_artifacts_s3_bucket[0])
            print(source_bucket)
            print(destination_bucket)

            for s3_object in source_bucket.objects.filter(Prefix=bootstrap_artifacts_key):
                destination_key = s3_object.key
                print(destination_key)
                s3.Object(destination_bucket.name, destination_key).copy_from(CopySource={
                                                                                        'Bucket': s3_object.bucket_name,
                                                                                        'Key': s3_object.key})
