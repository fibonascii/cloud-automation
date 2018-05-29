#Add repo key to server
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
#Download repo and add it to the repo list
sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
#Update repo
sudo yum update -y
#Install Jenkins and Java
sudo yum install -y java-1.8.0-openjdk jenkins
#Start jenkins
sudo service jenkins start
#Enable Jenkins on boot
sudo chkconfig jenkins on
#Remove outdated Java
sudo yum remove -y java-1.7.0-openjdk
#Grab jenkins secret
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
#Install Git
sudo yum install -y git
#Install hipchat-cli
git clone https://github.com/hipchat/hipchat-cli.git

