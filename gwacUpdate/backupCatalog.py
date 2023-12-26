# -*- coding: utf-8 -*-
import os
import paramiko
import time
from datetime import datetime, timedelta
import time
import traceback


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
    for i in range(2,5):
        for j in range(1,5):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
def backupDir(spath, dpath, logpath, ssh, ftp, ip, stopDateStr):
    
    fpackEXE = '/home/gwac/img_diff_xy/image_diff/tools/cfitsio/fpack'
    tempDirName = "G004_019_170617"
    tempFitsName = "G041_mon_objt_180210T10480999.fit.fz"
    stopDateNumber = int(stopDateStr)
    
    print("backup %s: %s"%(ip, spath))  
    ftp.chdir(spath)
    tdirs = ftp.listdir()
    tdirs.sort()
    dataDirs = []
    for tdir in tdirs:
        if tdir[0]==tempDirName[0] and tdir[4]==tempDirName[4] and tdir[8]==tempDirName[8] and len(tdir)==len(tempDirName):
            tdateStr = tdir[-6:]
            tdateNumber = int(tdateStr)
            if tdateNumber<stopDateNumber and tdateNumber> 190623: #备份今天之前的所有数据，不备份今天的数据
                dataDirs.append(tdir)

    if len(dataDirs)==0:
        return
    print("%s: %s total has %d dirs, lastDir is %s"%(ip, spath, len(dataDirs), dataDirs[-1]))  
    dataDirs.sort()
    
    continueFileName = ""
    continueFlag = False
    logfName0 = '%s/%s_%s.log'%(logpath, ip, os.path.basename(spath))
    ''''''
    if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
        tlastLine = getLastLine(logfName0)
        if len(tlastLine)>2:
            continueFileName=tlastLine.strip()
    
    tstr = "%s, last backup dir is %s, latest dir is %s"%(spath, continueFileName, dataDirs[-1])
    print(tstr)
    
    logfile0 = open(logfName0, 'a')
    #logfile0.write("190623\n\n")
    
    for tdir in dataDirs:
        
        #G002_023_171208
        dateStr = tdir[-6:]
        ccdStr = tdir[:8]
        
        if len(dateStr)==len(continueFileName) and dateStr>continueFileName:
            #tstr = "%s, %s start backup %s"%(spath, ccdStr, dateStr)
            #print(tstr)
            
            #break
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
                # tcmd = "cd %s ; tar -c *.fit.fz | ssh gwac@172.28.8.8 'tar -xvf - -C %s'"%(spath2,dpath2)
                # print(tcmd)
                # stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
                # for line in iter(stdout.readline, ""):
                #     print(line)
                
                tcmd = "ssh  -o PubkeyAcceptedKeyTypes=+ssh-rsa \
                    gwac@%s 'cd %s ; tar -c %s' | tar x -C %s"%(ip, spath,tdir, dpath)
                os.system(tcmd)

            except Exception as e:
                tstr = "backup %s error: %s"%(spath2, str(e))
                print(tstr)
                tstr = traceback.format_exc()
                print(tstr)
            
            ftp.chdir(spath2)
            tfiles = ftp.listdir()
            tfiles.sort()
            imgfiles = []
            for tfile in tfiles:
                if tfile[-6:]==tempFitsName[-6:]:
                    imgfiles.append(tfile)
                            
            ii = 0
            for timgName in imgfiles:
                localpath   = '%s/%s'%(dpath2, timgName)        
                if os.path.exists(localpath):
                    ii = ii + 1
             
            endTime = datetime.now()
            remainSeconds =(endTime - startTime).total_seconds()
            tstr = "%s total has %d files, success copyed %d files, use %d seconds, %.2fMB/s"%(tdir, len(imgfiles), ii, remainSeconds, ii*16.0/remainSeconds)
            print(tstr)
            
    logfile0.close()


def backupAllMachine():
    
    spath1 = '/data/GWAC/OutTable'
    
    dpath = '/data/databack/catalog/gwacCatalog'
    logpath = '/data/databack/catalog/gwacCatalog/gwac_backup_log'
    
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
        try:
            ssh.connect(tip, username=sftpUser, password=sftpPass)        
            ftp = ssh.open_sftp()
            backupDir(spath1, dpath, logpath, ssh, ftp, tip, curDateStr)
            
        except paramiko.AuthenticationException:
            print("Authentication Failed!")
            tstr = traceback.format_exc()
            print(tstr)
        except paramiko.SSHException:
            print("Issues with SSH service!")
            tstr = traceback.format_exc()
            print(tstr)
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
        try:
            time.sleep(1)
            ftp.close()
            ssh.close()
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        #break

    

if __name__ == '__main__':
    
    backupAllMachine()
    
    