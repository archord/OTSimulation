# -*- coding: utf-8 -*-
import os
import paramiko
import time
from datetime import datetime, timedelta
import time

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(2,5):
        if i==3:
            continue
        for j in range(1,5):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
def backupDir(ssh, ftp, ip):
    
    spath = '/data/gwac_diff_xy/data'
    dpath = '/data/work/diff_minorplanet'
    
    types1 = ['mpimgt','totimg','fotimg']
    types2 = ['mpt','tot']
    
    ftp.chdir(spath)
    tdirs = ftp.listdir()
    tdirs.sort()
    for tdir in tdirs:
        
        for tp in types1:
            spath2 = "%s/%s/J_subImg"%(spath, tdir)
            dpath2 = "%s/J_subImg_%s/%s"%(dpath, tp, tdir)
            if not os.path.exists(dpath2):
                os.makedirs(dpath2)
            
            tstr = "backup %s.npz of %s ..."%(tp, spath2)
            print(tstr)
            
            startTime = datetime.now()
            try:
                tcmd = "cd %s ; tar -c *%s.npz | ssh gwac@172.28.8.8 'tar -xf - -C %s'"%(spath2,tp, dpath2)
                print(tcmd)
                stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
                for line in iter(stdout.readline, ""):
                    print(line)
            except Exception as e:
                tstr = "backup %s error: %s"%(spath2, str(e))
                print(tstr)
            
            endTime = datetime.now()
            remainSeconds =(endTime - startTime).total_seconds()
            tstr = "total use %d seconds"%(remainSeconds)
            print(tstr)


        for tp in types2:
            spath2 = "%s/%s/J_subImgPreview"%(spath, tdir)
            dpath2 = "%s/J_subImgPreview_%s/%s"%(dpath, tp, tdir)
            if not os.path.exists(dpath2):
                os.makedirs(dpath2)
            
            tstr = "backup %s.jpg of %s ..."%(tp, spath2)
            print(tstr)
            
            startTime = datetime.now()
            try:
                tcmd = "cd %s ; tar -c *%s.jpg | ssh gwac@172.28.8.8 'tar -xf - -C %s'"%(spath2,tp, dpath2)
                print(tcmd)
                stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
                for line in iter(stdout.readline, ""):
                    print(line)
            except Exception as e:
                tstr = "backup %s error: %s"%(spath2, str(e))
                print(tstr)
            
            endTime = datetime.now()
            remainSeconds =(endTime - startTime).total_seconds()
            tstr = "total use %d seconds"%(remainSeconds)
            print(tstr)
        
        
def backupAllMachine():
    
    #sftpUser  =  'gwac'
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    ips = getIpList()
            
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
        
    for tip in ips:
        
        tstr = "start backup %s"%(tip)
        print(tstr)
        
        try:
            ssh.connect(tip, username=sftpUser, password=sftpPass)        
            ftp = ssh.open_sftp()
            backupDir(ssh, ftp, tip)
        except paramiko.AuthenticationException:
            print("Authentication Failed!")
        except paramiko.SSHException:
            print("Issues with SSH service!")
        except Exception as e:
            print(str(e))
        
        try:
            time.sleep(1)
            ftp.close()
            ssh.close()
        except Exception as e:
            print(str(e))
    

if __name__ == '__main__':
    
    tstr = "start gwac fits backup"
    print(tstr)
    backupAllMachine()
    
