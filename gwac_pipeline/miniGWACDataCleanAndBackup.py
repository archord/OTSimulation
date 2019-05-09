# -*- coding: utf-8 -*-
import time
import traceback
import os

def removeTmpData(spath, dpath):
    
    #rmDirs = ['cfgfile','imgstatus','origimage','otfollowlist','otlist','otlistsub','starlist','varlist']
    keepDirs = ['cutimages','otfollowimg']
    
    tdirs = os.listdir(spath)
    tDateDirs = []
    for tdir in tdirs:
        if tdir[0]=='1' and len(tdir)==6:
            tDateDirs.append(tdir)
    tDateDirs.sort()
    for tdir in tDateDirs:
        print("process %s"%(tdir))
        sDirs = "%s/%s"%(spath, tdir)
        #dDirs = "%s/%s"%(dpath, tdir)
        
        machines = os.listdir(sDirs)
        for tm in machines:
            sDirs2 = "%s/%s"%(sDirs, tm)
            tdataDirs = os.listdir(sDirs2)
            for tdataDir in tdataDirs:
                if tdataDir not in keepDirs:
                    sDirs3 = "%s/%s"%(sDirs2, tdataDir)
                    if os.path.exists(sDirs3):
                        os.system("rm -rf %s"%(sDirs3))
        
        time.sleep(1)
        
def batchCopy(spath, dpath):
        
    tdirs = os.listdir(spath)
    tDateDirs = []
    for tdir in tdirs:
        if tdir[0]=='1' and len(tdir)==6:
            tDateDirs.append(tdir)
    tDateDirs.sort()
    for tdir in tDateDirs:
        print("process %s"%(tdir))
        try:
            tcmd = "cd %s ; tar -c %s | ssh gwac@172.28.8.8 'tar -xf - -C %s'"%(spath,tdir, dpath)
            print(tcmd)
            os.system(tcmd)
        except Exception as e:
            tstr = "backup %s error: %s"%(tdir, str(e))
            print(tstr)
            tstr = traceback.format_exc()
            print(tstr)
        
        time.sleep(1)

if __name__ == '__main__':
    
    #spath = '/data/gwac_data'
    #dpath = '/data/mini_gwac_data'
    spath = '/data/gwac_data/mini-gwac-data-backup'
    dpath = '/data/mini_gwac_data/mini-gwac-data-backup'
    
    #removeTmpData(spath, dpath)
    batchCopy(spath, dpath)
    
