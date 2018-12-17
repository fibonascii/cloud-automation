# cloud-automation

## prerequisites to automated bulid/deploy

* Jenkins master running in the same region as we're deploying to
* Make sure Jenkins master is able to access this repository (saved credentials)
* Create a branch of this repo for each new environment and name it with org-region-uid. All config changes specific to this environment should be only pushed to the new branch
* Ami images to be deployed are accessible by this account in the same region.
  * If needed, copy ami's into the same region and add permission for the receiving account # to access it
  * Replace 
* Create a pd-cicd-devolopment key pair
* Create IAM role cicd-admin-role with AdministratorAccess to EC2
* Create an S3 bucket in a new account and sync pd-dev-cicd-artifacts into the new bucket. Replace pd-dev-cicd-artifacts in sceptre yaml files with the new bucket name (CoreBootStrapRepositoryS3BucketName)
* Update official kong ami id to match desired region
* If manifest is needed, make sure the ami id is correct
* Replace us-east-1 in all yaml files with the desired region (same for availability zones)
* Update WorkerNodeImageId as the one in master is located in east-1. This image is used to spin up EKS worker nodes
* Update cloudformation/lod-rest/templates/base.py to assure uniqueness of ClientCode, ClientEnvironmentKey and matching EnvironmentRegion. ClientEnvironmentKey is alphanumerical, 6 characters max
* Make sure to delete every incomplete environment with: sceptre delete-env ${ENV_NAME}. Otherwise there will be naming conflicts.