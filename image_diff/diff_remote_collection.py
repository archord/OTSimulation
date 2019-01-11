# -*- coding: utf-8 -*-
import paramiko
import time

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
        spath0= "%s/G00%s_0%s_190110/subImg"%(spath, ccdName[0],ccdName)   
        '''
        ftp = ssh.open_sftp()
        ftp.chdir(spath0)
        tfiles = ftp.listdir()
        tfiles.sort()
        
        badImgfiles = []
        fotImgfiles = []
        totImgfiles = []
        for tfile in tfiles:
            if tfile.find('bad')>-1:
                badImgfiles.append(tfile)
            elif tfile.find('fot')>-1:
                fotImgfiles.append(tfile)
            elif tfile.find('tot')>-1:
                totImgfiles.append(tfile)
        
        badNum = len(badImgfiles)
        totNum = len(totImgfiles)
        fotNum = len(fotImgfiles)
        if badNum>300:
            startIdx = 250
            endIdx = 300
        elif badNum>200:
            startIdx = 150
            endIdx = 200
        elif badNum>100:
            startIdx = 50
            endIdx = 100
        else:
            print("file number is %d"%(badNum))
            continue
        
        i = 0
        for tfile2 in badImgfiles:
            if i>=startIdx:
                remotepath = '%s/%s'%(spath0, tfile2)
                localpath = '%s/%s'%(dpath, tfile2)
                ftp.get(remotepath,localpath)
                
            if i>endIdx:
                break
            i=i+1
        i = 0
        for tfile2 in fotImgfiles:
            if i>=startIdx:
                remotepath = '%s/%s'%(spath0, tfile2)
                localpath = '%s/%s'%(dpath, tfile2)
                ftp.get(remotepath,localpath)
            if i>endIdx:
                break
            i=i+1
    
        ftp.close()
        '''
        try:
            tcmd = "cd %s ; tar -c *totimg.npz | ssh gwac@172.28.8.8 'tar -xf - -C %s'"%(spath0,dpath)
            print(tcmd)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                print(line)
        except Exception as e:
            tstr = "backup %s error: %s"%(spath0, str(e))
            print(tstr)
        
        time.sleep(1)
        ssh.close()
        #break

if __name__ == '__main__':
    
    #/data/gwac_diff_xy/data/G002_021_190110/subImg
    spath = r'/data/gwac_diff_xy/data'
    dpath = r'/data/work/ot2_img_collection_20190110'
    
    batchCopy(spath, dpath)
    batchCopy(spath, dpath)
    
