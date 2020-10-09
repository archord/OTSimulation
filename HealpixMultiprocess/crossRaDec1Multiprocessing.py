# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import multiprocessing
import pandas as pd

def getGreatCircleDistance(ra1, dec1, ra2, dec2):
    rst = 57.295779513 * math.acos(math.sin(0.017453293 * dec1) * math.sin(0.017453293 * dec2)
            + math.cos(0.017453293 * dec1) * math.cos(0.017453293 * dec2) * math.cos(0.017453293 * (math.fabs(ra1 - ra2))));
    return rst    

def getData1():
    
    tpath = '/data/work/hjtian/QSOs_NINA.txt'
    tdata=np.loadtxt(tpath,dtype='str') #, delimiter=' '
    raDec=tdata[:,0:2].astype(np.float)
    return raDec
    
def domatch(raDec0, tGPS1, tmatched, i, batchNum, total):
    
    maxDist = 3.0/60/60
    
    start = i*batchNum
    end = (i+1)*batchNum
    if end>total:
        end=total
    
    for i in range(start, end):
        
        try:
            td = tGPS1[i]
            ra1=td[1]
            dec1=td[2]
            if i%1000==0:
                print("%d, ra1=%f,dec1=%f"%(i, ra1,dec1))
            
            tidx1 = np.abs(raDec0[:,1]-dec1)<=maxDist
            raDec1 = raDec0[tidx1]
            for td2 in raDec1:
                ra2=td2[0]
                dec2=td2[1]
                dec1A=np.abs(dec1)
                dec2A=np.abs(dec2)
                maxDec = dec1A
                if dec2A>maxDec:
                    maxDec = dec2A
                if maxDec<60:
                    raDiff = np.abs(ra1-ra2)
                    tdist0 = raDiff*math.cos(maxDec)
                    if tdist0>maxDist*2:
                        continue
                
                tdist = getGreatCircleDistance(ra1, dec1, ra2, dec2)
                if tdist<=maxDist:
                    print("ra1=%f,dec1=%f, ra2=%f,dec2=%f, tdist=%f, maxDist=%f"%(ra1,dec1, ra2,dec2, tdist, maxDist))
                    tmatched[i]=1
        except Exception as e:
            print("domatch error")
            print(str(e))

def tmatch():
    
    raDec0 = getData1()
    
    root = '/data/work/hjtian/combine20191031'
    destDir = '/data/work/hjtian/crossmatch20200112'
    if not os.path.exists(destDir):
        os.system("mkdir -p %s"%(destDir))
    
    threadNum = 20
    p = multiprocessing.Pool(processes=threadNum)
  
    dirs = os.listdir(root)
    for tdir in dirs:
        
        tdataPath = "%s/%s"%(root,tdir)
        print(tdataPath)
        
        try:
            #GPS1_combine0_all_57198196.npz
            tstr00 = tdir.split('_')
            print(tstr00[3])
            tdata00 = np.load(tdataPath)
            tGPS1=tdata00['datas']
            
            tNum = tGPS1.shape[0]
            tBatch = int(tNum/20)+1
            tmIdxs = np.zeros(tNum)
            for i in range(threadNum):
                p.apply_async(domatch, args=(raDec0, tGPS1, tmIdxs, i, tBatch, tNum))
            
            p.close()
            p.join()
            tmatched = tGPS1[tmIdxs>0]
            if tmatched.shape[0]>0:
                savePath = '%s/%s'%(destDir,tdir)
                GPS1_df = pd.DataFrame(tmatched)
                GPS1_df.to_csv(savePath, index=False)
            
        except Exception as e:
            print(str(e))
        #break


if __name__ == "__main__":
    
    tmatch()
    
    