# -*- coding: utf-8 -*-
import sys
import paramiko
import time
from datetime import datetime

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(2,5):
        for j in range(1,5):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
if __name__ == '__main__':
    
    if len(sys.argv)==2:
        cmdName = sys.argv[1] #start stop status
    else:
        cmdName = "status"
    
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
        
    dpathProgram = r'/home/gwac/img_diff_xy'
    pythonPath = '%s/anaconda3/envs/imgdiff3/bin/python'%(dpathProgram)
    diffDaemonLog = 'diffDaemonLog.txt'
    procName = "BatchDiff"
    
    ips = getIpList()
        
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    
    loopNum = 1
    while True:
        
        logfile0 = open(diffDaemonLog, 'a')
        timeStr = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        logfile0.write("\n%06d loop: %s\n"%(loopNum, timeStr))
        logfile0.flush()
        
        for ip in ips:
            
            ssh.connect(ip, username=sftpUser, password=sftpPass)
            
            pid = -1
            is2Alive = False
            stdin, stdout, stderr = ssh.exec_command('ps aux | grep %s'%(procName), get_pty=True)
            for line in iter(stdout.readline, ""): 
                if line.find("%s.py"%(procName))>-1 and line.find("imgdiff3")>-1:
                    strArr = line.split()
                    if len(strArr)>1:
                        pid = int(strArr[1])
                    is2Alive = True       
                    break
                
            if is2Alive:
                tstr = "%s %s.py is running\n"%(ip, procName)
                print(tstr)
                logfile0.write(tstr)
                logfile0.flush()
            else:
                tstr = "%s %s.py is not running\n"%(ip, procName)
                print(tstr)
                logfile0.write(tstr)
                logfile0.flush()
                
            if not is2Alive and cmdName == "start":
                logfile0.write("%s %s.py is not running, rerun\n"%(ip,procName))
                logfile0.flush()
                camName = "G0%s"%(ip[-2:])
                tcommand = 'cd %s/image_diff ; nohup %s %s.py %s > log1.txt &'%(dpathProgram, pythonPath, procName, camName)
                ssh.exec_command(tcommand)
                
            if is2Alive and cmdName == "stop" and pid>0:
                tstr = "%s %s.py is running, kill %d\n"%(ip,procName,pid)
                print(tstr)
                logfile0.write(tstr)
                logfile0.flush()
                tcommand = 'kill -9 %d'%(pid)
                ssh.exec_command(tcommand)
                
            time.sleep(1)
            ssh.close()
            logfile0.flush()
        
        loopNum = loopNum + 1
        if loopNum>1:
            break
        logfile0.close()
        time.sleep(60*5)
        