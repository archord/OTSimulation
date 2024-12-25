# -*- coding: utf-8 -*-
import os
import paramiko
import time
import hashlib

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(1,11):
        for j in range(1,6):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips

    
def doAllMachine():
        
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    ips = getIpList()
    destRootDir = '/home/gwac/.ssh'
            
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    
    for tip in ips:
        
        print("start batch ssh-keygen %s"%(tip))
        
        try:
            ssh.connect(tip, username=sftpUser, password=sftpPass)
            tcmd = f'rm -rf {destRootDir} && mkdir -p {destRootDir}'
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
            
            tcmd = f'ssh-keygen -q -N "" -f {destRootDir}/id_rsa'
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
            
            
            print(f'{destRootDir}/id_rsa.cache')
            ftp = ssh.open_sftp()
            ftp.put(f'/home/gwac/.ssh/id_rsa.pub',f'{destRootDir}/id_rsa.cache')
            ftp.close()
            # os.system("cat /home/gwac/.ssh/id_rsa.cache >> /home/gwac/.ssh/authorized_keys")
            # os.system("rm -rf /home/gwac/.ssh/id_rsa.cache")
            
            tcmd = f'cat {destRootDir}/id_rsa.cache >> {destRootDir}/authorized_keys'
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
                                
        except paramiko.AuthenticationException:
            print("Authentication Failed!")
        except paramiko.SSHException:
            print("Issues with SSH service!")
        except Exception as e:
            print(str(e))
        
        time.sleep(1)
        ssh.close()
        break

if __name__ == '__main__':
    
    
    doAllMachine()
    
    
