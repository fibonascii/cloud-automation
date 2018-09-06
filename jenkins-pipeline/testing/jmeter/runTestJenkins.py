'''
Created on Aug 29, 2018

@author: jalmanza
'''
from paramiko.client import SSHClient
from fabric import *
import paramiko
client = SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def launchSlave(strHostname , strUser, strPathToPemFile, strIpAddress):
    
    hostname = strHostname
    user = strUser
    key_filename = strPathToPemFile
    strCommand = 'ssh -t -i /home/'+strUser+'/jmeter.pem '+strUser+'@'+strIpAddress+' ./apache-jmeter-4.0/bin/jmeter-server >&- 2>&- <&- &'
    

    client.connect(hostname=hostname, port=22, username = user , key_filename=key_filename);
    
    client.exec_command(command = strCommand)
    
    print('Slave launched')
         
    

def launchMaster(strHostname , strUser, strPathToPemFile,strMasterIpAddress, strRemoteIpAddress):    
    hostname = strHostname
    user = strUser
    key_filename = strPathToPemFile
    strCommand = './apache-jmeter-4.0/bin/jmeter.sh -R '+strRemoteIpAddress+' -n -t ~/jmeterScript/ProdDev-Latest_LoadTest_unix2.jmx -l ~/jmeterResults/resultRemote.jtl -Djava.rmi.server.hostname='+strMasterIpAddress
    
    #strCommand = './apache-jmeter-4.0/bin/jmeter.sh -R '+strRemoteIpAddress+' -n -t ~/jmeterScript/HTTPRequest.jmx -l ~/jmeterResults/resultRemote.jtl -Djava.rmi.server.hostname='+strMasterIpAddress
   
    #print(strCommand)
    client.connect(hostname=hostname, port=22, username = user , key_filename=key_filename);
    
    stdin , stdout, stderr = client.exec_command(command = strCommand)
             
    print(stdout.read())
    print( "Errors")
    print(stderr.read())    

def cleanStopSlaves(strHostname , strUser, strPathToPemFile,strRemoteIpAddress):
    
    hostname = strHostname
    user = strUser
    key_filename = strPathToPemFile
    strCommand = 'ssh -tt -i /home/'+strUser+'/jmeter.pem '+strUser+'@'+strRemoteIpAddress+' ./apache-jmeter-4.0/bin/shutdown.sh'
            
    #print(strCommand)
    client.connect(hostname=hostname, port=22, username = user , key_filename=key_filename);
    
    stdin , stdout, stderr = client.exec_command(command = strCommand)
    print(stdout.read())
    print( "Errors")
    print(stderr.read())
    strCommand = 'ssh -tt -i /home/'+strUser+'/jmeter.pem '+strUser+'@'+strRemoteIpAddress+' "sudo fuser 1099/tcp -k"'
    stdin , stdout, stderr = client.exec_command(command = strCommand)
    print(stdout.read())
    print( "Errors")
    print(stderr.read())
    
    print('Shutdown Slave')

def copyFileTocreateTheReport(strHostname , strUser, strPathToPemFile,strPathFromRemoteResultsFile,strPathLocalResultFile):
    
    hostname = strHostname
    user = strUser
    key_filename = strPathToPemFile
            
    client.connect(hostname=hostname, port=22, username = user , key_filename=key_filename);    
    sftp = client.open_sftp()
    sftp.get(strPathFromRemoteResultsFile,strPathLocalResultFile)
    sftp.close()
    client.close()
    
    
    

strHost = 'M-JM-PUB-LB-D1DP-JM-615163677.us-east-1.elb.amazonaws.com'
strUser = 'ec2-user'
strPathToPem = '/var/jenkins_home/.ssh/jmeter.pem'
strSlave1Ip = '10.0.1.155'    
strMasterIp = '10.0.1.144'
strPathFromRemoteResultsFile = '/home/ec2-user/jmeterResults/resultRemote.jtl'
strPathLocalResultFile = '/var/jenkins_home/resultRemote.jtl'

launchSlave(strHost,strUser,strPathToPem,strSlave1Ip)

launchMaster(strHost,strUser,strPathToPem,strMasterIp,strSlave1Ip)

cleanStopSlaves(strHost,strUser,strPathToPem,strSlave1Ip)

copyFileTocreateTheReport(strHost,strUser,strPathToPem,strPathFromRemoteResultsFile,strPathLocalResultFile)
