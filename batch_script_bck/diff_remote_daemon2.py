# -*- coding: utf-8 -*-
import sys
import paramiko
import time
import subprocess
from datetime import datetime
import traceback

def getIpList():

    ipPrefix   =  '172.28.2.'

    ips = []
    for i in range(2,5):
        if i==3:
            continue
        for j in range(1,5):
            #if j==2:
            #    continue
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
def checkStatus(loopNum, cmdName, procName = "SchedulingSingle"):

    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
        
    dpathProgram = r'/home/gwac/img_diff_xy'
    pythonPath = '%s/anaconda3/envs/imgdiff3/bin/python'%(dpathProgram)
    diffDaemonLog = 'diffDaemonLog.txt'
    #procName = "BatchDiff"
    #procName = "Scheduling"
    #procName = "SchedulingSingle"
    #procName2 = "CreateWCSIndex_local"
    runName = "p1"
    
    ips = getIpList()
        
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    
    logfile0 = open(diffDaemonLog, 'a')
    timeStr = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    logfile0.write("\n%06d loop: %s\n"%(loopNum, timeStr))
    logfile0.flush()
    
    for ip in ips:
        
        try:
            ssh.connect(ip, username=sftpUser, password=sftpPass)
            
            pids = []
            is2Alive = False
            stdin, stdout, stderr = ssh.exec_command('ps aux | grep %s'%(procName), get_pty=True)
            for line in iter(stdout.readline, ""): 
                if line.find("%s.py"%(procName))>-1 and line.find("imgdiff3")>-1:
                    strArr = line.split()
                    if len(strArr)>1:
                        tpid = int(strArr[1])
                        pids.append(tpid)
                    is2Alive = True       
                    #break
                
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
                tstr = "%s %s.py is not running, rerun\n"%(ip,procName)
                print(tstr)
                logfile0.write(tstr)
                logfile0.flush()
                camName = "G0%s"%(ip[-2:])
                tcommand = 'cd %s/image_diff3_minorplanet; nohup %s %s.py %s %s > %s_log.txt & '%(dpathProgram, pythonPath, procName, camName, runName, procName)
                #print(tcommand)
                stdin, stdout, stderr = ssh.exec_command(tcommand)
                #print("print stdout")
                ##print(stdout.readlines())
                #print("print stderr")
                #print(stderr.readlines())
                #transport = ssh.get_transport()
                #channel = transport.open_session()
                #tcommand = 'cd %s/image_diff ; %s %s.py %s > log1.txt &'%(dpathProgram, pythonPath, procName, camName)
                #channel.exec_command(tcommand)
                
            if is2Alive and cmdName == "stop" and len(pids)>0:
                for pid in pids:
                    tstr = "%s %s.py is running, kill %d\n"%(ip,procName,pid)
                    print(tstr)
                    logfile0.write(tstr)
                    logfile0.flush()
                    tcommand = 'kill -9 %d'%(pid)
                    ssh.exec_command(tcommand)
                
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        time.sleep(1)
        ssh.close()
        #break
        
    logfile0.close()
        
if __name__ == '__main__':
    
    if len(sys.argv)==3:
        procName = sys.argv[1] #"SchedulingSingle"
        cmdName = sys.argv[2] #start stop status
    else:
        procName = "SchedulingSingle"
        cmdName = "status"
        print("default command is: diff_remote_daemon.py %s %s"%(procName, cmdName))
        
    if len(procName)<5 or procName=="*":
        print("procName %s is error, stop run."%(procName))
    
    if cmdName == "start":

        loopNum = 1
        while True:
            
            curUtcDateTime = datetime.utcnow()
            tDateTime = datetime.utcnow()
            startDateTime = tDateTime.replace(hour=0, minute=00, second=0)  #9=17  1=9
            endDateTime = tDateTime.replace(hour=22, minute=30, second=0)  #22=6    8=16
            remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
            remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
            if remainSeconds1<0 and remainSeconds2>0:
                
                try:
                    checkStatus(loopNum, cmdName, procName)
            
                except Exception as e:
                    print(str(e))
                    tstr = traceback.format_exc()
                    print(tstr)
                    
                loopNum = loopNum + 1
                #if loopNum>1:
                #    break
                time.sleep(60*20)
            else:
                time.sleep(60*5)
    else:
        checkStatus(1, cmdName, procName)
