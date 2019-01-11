# -*- coding: utf-8 -*-
import os
import paramiko
import time
import traceback

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(2,5):
        for j in range(1,5):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
if __name__ == '__main__':
    
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    
    programDir = 'image_diff'
    
    sroot = r'/data/work/program/image_diff_base'
    sanaconda2 = '%s/anaconda3.tar'%(sroot)
    sprogramDirTar = '%s/%s.tar'%(sroot, programDir)
    
    droot = r'/home/gwac/img_diff_xy'
    danaconda2 = '%s/anaconda2.tar'%(droot)
    dprogramDirTar = '%s/%s.tar'%(droot, programDir)
    
    os.system("rm -rf %s"%(sprogramDirTar))
    os.system("cd %s ; tar -cf %s.tar %s"%(sroot,programDir, programDir))
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
        
        ips = getIpList()
        for ip in ips:
            
            tnum = int(ip[-2:])
            #if tnum<24:
            #    continue
            
            print("process %s"%(ip))
            ssh.connect(ip, username=sftpUser, password=sftpPass)
            
            #tcommand = 'mkdir %s'%(droot)
            #print(tcommand)
            #stdin, stdout, stderr = ssh.exec_command(tcommand, get_pty=True)
            #for line in iter(stdout.readline, ""):
            #    print(line)
    
            ftp = ssh.open_sftp()
            #print("send %s"%(sanaconda2))
            #ftp.put(sanaconda2, danaconda2)
            print("send %s"%(sprogramDirTar))
            ftp.put(sprogramDirTar, dprogramDirTar)
            ftp.close()
            
            #ssh.exec_command('cd %s ; tar -xf %s'%(droot, danaconda2))
            ssh.exec_command('cd %s ; tar -xf %s'%(droot, dprogramDirTar))
            
            ssh.close()
            time.sleep(1)
        
    except Exception as e:
        print(e)
        tstr = traceback.format_exc()
        print(tstr)