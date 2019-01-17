# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
import os
import paramiko
import time
import hashlib
import requests
from datetime import datetime, timedelta
import time
from gwacDataClient import GWACDataClient


def sendMsg(msgSession, tmsg):
    
    try:
        sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        tmsg = "%s: %s"%(sendTime, tmsg)
        msgURL = "http://172.28.8.8:8080/gwebend/sendTrigger2WChart.action?chatId=gwac004&triggerMsg="
        turl = "%s%s"%(msgURL,tmsg)
        msgSession.get(turl, timeout=10, verify=False)
    except Exception as e:
        print(str(e))

def file_as_bytes(file):
    with file:
        return file.read()

#limit: require the file at least have two lines
def getLastLine(fname):
    f = open(fname, 'rb')
    last = ""
    try:
        f.seek(0, os.SEEK_END)
        if f.tell()>1:
            f.seek(-1, os.SEEK_END)     # Jump to the second last byte.
            tdata = f.read(1)
            #jump the last empty line, to the last line with content
            while tdata == b"\n" or tdata == b"\r":
                if f.tell()<=1:
                    break
                f.seek(-2, os.SEEK_CUR) 
                tdata = f.read(1)
            #search to the head of last line
            while tdata != b"\n" and tdata != b"\r":
                f.seek(-2, os.SEEK_CUR)
                tdata = f.read(1)
            last = f.readline().decode()         # Read last line.
            #last = f.readlines()[-1].decode()
    finally:
        f.close()
    return last.strip()

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    #for i in range(2,5):
    #    for j in range(1,6):
    for i in range(4,5):
        for j in range(2,4):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
def backupDir(spath, dpath, logpath, ssh, ftp, ip, msgSession, stopDateStr, dataClient):
    
    tempDirName = "G002_021_181217"
    tempFitsName = "G021_mon_objt_181214T13131212.Fcat"
    stopDateNumber = int(stopDateStr)
    
    ftp.chdir(spath)
    tdirs = ftp.listdir()
    tdirs.sort()
    dataDirs = []
    for tdir in tdirs:
        if tdir[0]==tempDirName[0] and tdir[4]==tempDirName[4] and tdir[8]==tempDirName[8] and len(tdir)==len(tempDirName):
            tdateStr = tdir[-6:]
            tdateNumber = int(tdateStr)
            if tdateNumber<=stopDateNumber and tdateNumber>= 180924:
                dataDirs.append(tdir)
                
    print("%s total has %d dirs"%(spath, len(dataDirs)))    
    continueFileName = ""
    continueFlag = False
    logfName0 = '%s/%s_%s.log'%(logpath, ip, os.path.basename(spath))
    if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
        tlastLine = getLastLine(logfName0)
        if len(tlastLine)>2:
            continueFileName=tlastLine.strip()
            
    logfile0 = open(logfName0, 'a')
    logfile0.write("\n\n")
    
    for tdir in dataDirs:
        
        #G002_023_171208
        dateStr = tdir[-6:]
        ccdStr = tdir[:8]
        
        #if (not continueFlag)  and len(tdir)==len(continueFileName):
        if (not continueFlag)  and len(dateStr)==len(continueFileName):
            if dateStr!=continueFileName:
                continue
            else:
                continueFlag = True
                print("last line is: %s, restart from next dir"%(continueFileName))
                continue
        
        #logfile0.write("%s\n"%(tdir))
        logfile0.write("%s\n"%(dateStr))
        logfile0.flush()
        
        spath2 = "%s/%s"%(spath, tdir)
        #dpath2 = "%s/%s"%(dpath, tdir)
        dpath2 = "%s/%s/%s"%(dpath, dateStr, ccdStr)
        if not os.path.exists(dpath2):
            os.makedirs(dpath2)
        
        tstr = "backup %s ..."%(spath2)
        print(tstr)
        
        startTime = datetime.now()
        try:
            tcmd = "cd %s ; tar -c *.Fcat | ssh gwaclc@190.168.1.197 'tar -xf - -C %s'"%(spath2,dpath2)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
        except Exception as e:
            tstr = "backup %s error: %s"%(spath2, str(e))
            print(tstr)
        
        print("copy to middle machine done, start transfer: ")
        #dataClient = GWACDataClient('10.0.82.111', '12626')
        totalImg, sendSuccess = dataClient.sendPath(dpath2, ssh)
        os.system("rm -rf %s"%(dpath2))
        
        #if totalImg>0:
        #    break
            
        endTime = datetime.now()
        remainSeconds =(endTime - startTime).total_seconds()
        tstr = "%s total has %d files, success copyed %d files, use %d seconds"%(tdir, totalImg, sendSuccess, remainSeconds)
        print(tstr)
        #sendMsg(msgSession, tstr)
            
    logfile0.close()
        
        
def backupAllMachine(msgSession):
    
    dataClient = GWACDataClient('10.0.82.111', '12626')
    dataClient.sendMsg('start')
    time.sleep(60)
    
    dataRoot = os.getcwd()
    spath1 = '/data/GWAC/OutTable'
    dpath = '%s/tmp'%(dataRoot)
    logCletpath = '%s/log_collect'%(dataRoot)
    logSendpath = '%s/log_send'%(dataRoot)
    
    if not os.path.exists(logCletpath):
        os.mkdir(logCletpath)
    if not os.path.exists(logSendpath):
        os.mkdir(logSendpath)
    
    curDateTime = datetime.now()
    curDateTime = curDateTime - timedelta(days=1)
    curDateStr = datetime.strftime(curDateTime, "%Y%m%d")
    curDateStr = curDateStr[2:]
    
    #sftpUser  =  'gwac'
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    ips = getIpList()
            
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
        
    for tip in ips:
        
        tstr = "start backup %s"%(tip)
        print(tstr)
        #sendMsg(msgSession, tstr)
        try:
            ssh.connect(tip, username=sftpUser, password=sftpPass)        
            ftp = ssh.open_sftp()
            backupDir(spath1, dpath, logCletpath, ssh, ftp, tip, msgSession, curDateStr, dataClient)
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
        #break
    
    dataClient.sendMsg('start')

if __name__ == '__main__':
    
    while True:
        try:
            curDateTime = datetime.now()
            tDateTime = datetime.now()
            startDateTime = tDateTime.replace(hour=7, minute=0, second=0)
            endDateTime = tDateTime.replace(hour=17, minute=0, second=0)
            remainSeconds1 = (startDateTime - curDateTime).total_seconds()
            remainSeconds2 = (endDateTime - curDateTime).total_seconds()
            if remainSeconds1<0 and remainSeconds2>0:
                msgSession = requests.Session()
                tstr = "start gwac fits backup"
                print(tstr)
                #sendMsg(msgSession, tstr)
                backupAllMachine(msgSession)
                time.sleep(1*60*60)
                tstr = "backup done"
                print(tstr)
                #sendMsg(msgSession, tstr)
            else:
                time.sleep(10*60)
        except Exception as e:
            print(str(e))
        break
    
