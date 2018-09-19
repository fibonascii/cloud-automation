#!/bin/bash
CLIENT_CODE_TAG="ClientCode"
INSTANCE_ID="$(curl http://169.254.169.254/latest/meta-data/instance-id)"
echo $INSTANCE_ID

REGION="us-east-1"
echo $REGION
CLIENT_CODE_VALUE="$(aws ec2 describe-tags --filters "Name=resource-id,Values=${INSTANCE_ID}" "Name=key,Values=${CLIENT_CODE_TAG}" --region ${REGION} --output=text | cut -f5)"
echo $CLIENT_CODE_VALUE

KongVersionSSMKey="-KongVersion"
KongVersionSSMKey=${CLIENT_CODE_VALUE}${KongVersionSSMKey}
echo $KongVersionSSMKey
kong_version="$(aws ssm get-parameter --name ${KongVersionSSMKey} --region ${REGION} --output text --query 'Parameter.Value')"
echo $kong_version

CassandraSeedListSSMKey="-CassandraSeedList"
CassandraSeedListSSMKey=${CLIENT_CODE_VALUE}${CassandraSeedListSSMKey}
echo $CassandraSeedListSSMKey
CASSANDRA_HOSTS="$(aws ssm get-parameter --name ${CassandraSeedListSSMKey} --region ${REGION} --output text --query 'Parameter.Value')"
echo $CASSANDRA_HOSTS

KongExecuteMigrationsSSMKey="-KongExecuteMigrations"
KongExecuteMigrationsSSMKey=${CLIENT_CODE_VALUE}${KongExecuteMigrationsSSMKey}
echo KongExecuteMigrationsSSMKey
kong_migrations="$(aws ssm get-parameter --name ${KongExecuteMigrationsSSMKey} --region ${REGION} --output text --query 'Parameter.Value')"
echo $kong_migrations

echo '* soft nofile 65000' >> /etc/security/limits.conf
echo '* hard nofile 65000' >> /etc/security/limits.conf

if [ "$kong_version" != "" ]
then
   kong_version="-$kong_version"
fi
echo $kong_version

CASSANDRA_HOSTS=("10.0.1.132")
for i in "${CASSANDRA_HOSTS[@]}"
do
   CASSANDRA_HOST_LIST+="$i," 
done

CASSANDRA_HOST_LIST=${CASSANDRA_HOST_LIST:0:${#CASSANDRA_HOST_LIST}-1}
echo $CASSANDRA_HOST_LIST

mkdir /usr/local/kong && chown ec2-user /usr/local/kong
wget https://bintray.com/kong/kong-community-edition-aws/rpm -O bintray-kong-kong-community-edition-aws.repo
mv bintray-kong-kong-community-edition-aws.repo /etc/yum.repos.d/
yum update -y
yum install -y epel-release
yum install -y kong-community-edition$kong_version --nogpgcheck
echo "admin_listen=0.0.0.0:8001,0.0.0.0:8444 ssl
database=cassandra
cassandra_contact_points="$CASSANDRA_HOST_LIST"
cassandra_username=cassandra
cassandra_password=cassandra" >> /etc/kong/kong.conf

if [ "$kong_migrations" == "true" ]
then
 echo "[kong] starting migrations..."
 su -s /bin/sh -c "/usr/local/bin/kong migrations up" ec2-user
 aws ssm put-parameter --name $KongExecuteMigrationsSSMKey --type "String" --overwrite --region $REGION --value "false"
fi
su -s /bin/sh -c "/usr/local/bin/kong start" ec2-user
su -s /bin/sh -c "/usr/local/bin/kong health" ec2-user

