# -*- coding: utf-8 -*-
#Web服务器数据迁移
import os
import paramiko
import time
from datetime import datetime, timedelta
import time
import traceback

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
    
def backupDir(spath, dpath, logpath, ssh, ftp, ip, stopDateStr):
    
    fpackEXE = '/home/gwac/img_diff_xy/image_diff/tools/cfitsio/fpack'
    tempDirName = "20170617"
    tempFitsName = "G041_mon_objt_180210T10480999.fit.fz"
    
    print("backup %s: %s"%(ip, spath))  
    ftp.chdir(spath)
    tdirs = ftp.listdir()
    tdirs.sort()
    dataDirs = []
    for tdir in tdirs:
        if tdir[0:2]=='20' and len(tdir)==len(tempDirName):
            tdateNumber = int(tdir)
            if tdateNumber<20231204:
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
    else:
        continueFileName = "20170929"
    
    tstr = "%s, last backup dir is %s, latest dir is %s"%(spath, continueFileName, dataDirs[-1])
    print(tstr)
    
    logfile0 = open(logfName0, 'a')
    #logfile0.write("20190623\n\n")
    
    for tdir in dataDirs:
        
        #20171208
        dateStr = tdir
        
        if len(dateStr)==len(continueFileName) and dateStr>continueFileName:
            #tstr = "%s, %s start backup %s"%(spath, ccdStr, dateStr)
            #print(tstr)
            
            #break
            #logfile0.write("%s\n"%(tdir))
            logfile0.write("%s\n"%(dateStr))
            logfile0.flush()
            
            spath2 = "%s/%s"%(spath, tdir)
            dpath2 = "%s/%s"%(dpath, tdir)
            if not os.path.exists(dpath2):
                os.makedirs(dpath2)
            
            tstr = "backup %s ..."%(spath2)
            print(tstr)
            
            startTime = datetime.now()
            try:
                # tcmd = "cd %s ; tar -c *.fit.fz | ssh gwac@172.28.8.8 'tar -xvf - -C %s'"%(spath2,dpath2)
                # ssh  -o PubkeyAcceptedKeyTypes=+ssh-rsa \
                # gwac@172.28.8.8 "cd /data/gwac_data ; tar -c 20170930" | tar x -C /data/gwac_data
                tcmd = "ssh  -o PubkeyAcceptedKeyTypes=+ssh-rsa \
                    gwac@172.28.8.8 'cd %s ; tar -c %s' | tar x -C %s"%(spath,tdir, dpath)
                # tcmd = "cd %s ; tar -c %s | ssh gwac@172.28.8.9 'tar -xvf - -C %s'"%(spath,tdir, dpath)
                # print(tcmd)
                # stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
                # for line in iter(stdout.readline, ""):
                #     print(line)
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

        # break
            
    logfile0.close()
        
def backupAllMachine():
    
    # spath = '/data/gwac_data/gwac_orig_fits'
    spath = '/data/gwac_data'
    dpath = '/data/gwac_data'
    # dpath = '/Users/xy/gwac_data'
    logpath = '/data/gwac_data/gwac_backup_log'
    
    curDateTime = datetime.now()
    curDateTime = curDateTime - timedelta(days=1)
    curDateStr = datetime.strftime(curDateTime, "%Y%m%d")
    curDateStr = curDateStr[2:]
    
    sftpUser  =  'gwac'
    sftpPass  =  'xyag902'
            
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
        
    tip = "172.28.8.8"
    # tip = "10.0.10.236"
    tstr = "start backup %s"%(tip)
    print(tstr)
    
    try:
        ssh.connect(tip, username=sftpUser, password=sftpPass)        
        ftp = ssh.open_sftp()
        backupDir(spath, dpath, logpath, ssh, ftp, tip, curDateStr)
        
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
    
    