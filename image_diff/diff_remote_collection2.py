# -*- coding: utf-8 -*-
import paramiko
import time
from datetime import datetime
import traceback

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(2,5):
        for j in range(1,5):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips

def batchCopy(spath, dpath):
    
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
        
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    
    ips = getIpList()
    for ip in ips:
        
        print("process %s"%(ip))
        ssh.connect(ip, username=sftpUser, password=sftpPass)    
        
        ccdName = ip[-2:]
        dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
        dateStr = dateStr[2:]
        dateStr = '190113'
        dirName1 = "G00%s_0%s_%s"%(ccdName[0],ccdName,dateStr)
        dirName2 = "G00%s_0%s_190112"%(ccdName[0],ccdName)
        
        try:
            
            tcmd = "cd %s ; tar -c %s | ssh gwac@172.28.8.8 'tar -xf - -C %s/%s'"%(spath,dirName1, dpath, dateStr)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
            tcmd = "cd %s ; tar -c %s | ssh gwac@172.28.8.8 'tar -xf - -C %s/%s'"%(spath,dirName2, dpath, dateStr)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
            '''
            tcmd = "cd %s ; rm -rf %s %s %s"%(spath,dirName1, dirName2)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
            '''    
        except Exception as e:
            tstr = "backup %s %s error: %s"%(ip, dirName1, str(e))
            print(tstr)
            tstr = traceback.format_exc()
            print(tstr)
        
        time.sleep(1)
        ssh.close()
        #break


def batchCopy2(spath, dpath):
    
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
        
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    
    ips = getIpList()
    for ip in ips:
        
        print("process %s"%(ip))
        ssh.connect(ip, username=sftpUser, password=sftpPass)    
        dateStr = '20190116'
        
        try:
            '''
            tcmd = "cd %s ; tar -c G00* | ssh gwac@172.28.8.8 'tar -xf - -C %s/%s'"%(spath, dpath, dateStr)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
            '''
            tcmd = "cd %s ; rm -rf G00* "%(spath)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
        except Exception as e:
            tstr = "backup %s error: %s"%(ip, str(e))
            print(tstr)
            tstr = traceback.format_exc()
            print(tstr)
        
        time.sleep(1)
        ssh.close()
        #break
        
if __name__ == '__main__':
    
    #/data/gwac_diff_xy/data/G002_021_190110/subImg
    spath = r'/data/gwac_diff_xy/data'
    dpath = r'/data/work/diff_img'
    
    batchCopy2(spath, dpath)
    
