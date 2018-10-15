# Install Jenkins Job Builder

install:
	mkdir /etc/jenkins_jobs
	mv config/jenkins_jobs.ini /etc/jenkins_jobs/
	mv jobs /etc/jenkins_jobs/
	chown -R jenkins.jenkins /etc/jenkins_jobs
	git clone https://git.openstack.org/openstack-infra/jenkins-job-builder
	pip3 install -r jenkins-job-builder/requirements.txt
	(cd /opt/make/jobbuilder/jenkins-job-builder && python3 setup.py install)
deploy:
	jenkins-jobs --conf /etc/jenkins_jobs/jenkins_jobs.ini update /etc/jenkins_jobs/jobs/


