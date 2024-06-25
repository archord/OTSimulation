# -*- coding: utf-8 -*-
import paramiko
import time
import os

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(1,5):
        if i!=1:
            continue
        for j in range(1,6):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips

def getIpList2():
    
    ipPrefix   =  '172.28.100.'
    
    ips = []
    for i in range(1,14):
        if i not in (7,9):
            continue
        ip = "%s%d"%(ipPrefix, i)
        ips.append(ip)
    return ips

def doShutdown():
        
    sftpUser  =  'gwac'
    sftpPass  =  '123456' #gwac1234 123456
        
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    
    ips = getIpList2()
    for ip in ips:
        
        try:
            print("process %s"%(ip))
            ssh.connect(ip, username=sftpUser, password=sftpPass, timeout=2) 
            
            tcmd = "sudo shutdown -h now"
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)

            # 通过stdin管道输入密码并添加换行符
            stdin.write(sftpPass + '\n')
            stdin.flush()
            
            # 等待命令执行完成
            time.sleep(1)

            for line in iter(stdout.readline, ""):
                print(line)
            
        except Exception as e:
            tstr = "doShutdown %s error: %s"%(ip, str(e))
            print(tstr)
        
        time.sleep(1)
        ssh.close()
        #break

if __name__ == '__main__':
    
    doShutdown()    

