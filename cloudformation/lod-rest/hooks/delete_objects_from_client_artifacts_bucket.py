from sceptre.hooks import Hook
from sceptre.stack import Stack
import boto3


class DeleteObjectsFromClientArtifactsBucket(Hook):

    def __init__(self, *args, **kwargs):
        super(DeleteObjectsFromClientArtifactsBucket, self).__init__(*args, **kwargs)

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
            client_artifacts_s3_bucket_name = [output['OutputValue'] for output in outputs if
                                               output['OutputKey'] == 'EnvironmentArtifactsS3Bucket']
            print(client_artifacts_s3_bucket_name[0])

            s3 = boto3.resource('s3')
            for bucket in s3.buckets.all():
                print(bucket.name)
                if bucket.name == client_artifacts_s3_bucket_name[0]:
                    bucket.object_versions.delete()
