# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime
import traceback
from astropy.io import fits
import math

def superCombine(srcFitDir, destFitDir, cmbNum = 5, regions=[2,2]):

    try:
        if not os.path.exists(destFitDir):
            os.system("mkdir -p %s"%(destFitDir))
            
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            tfiles.append(tfile)
        
        #tnum = len(tfiles)-1
        tnum = len(tfiles)
        if cmbNum<0:
            cmbNum = tnum
        totalCmb = math.floor(tnum*1.0/cmbNum)
        print("total cmb %d"%(totalCmb))
        for i in range(totalCmb):
            
            starttime = datetime.now()
            tCmbImg = np.array([])
            regWid = 0
            regHei = 0
            for ty in range(regions[0]):
                for tx in range(regions[1]):
                    imgs = []
                    for j in range(0,cmbNum):
                        tIdx = i*cmbNum+j
                        #tIdx = tnum - (i*cmbNum+j)
                        if tIdx > tnum-1 or tIdx <0:
                            break
                        tname = tfiles[tIdx]
                        print("read %d, %s"%(tIdx, tname))
                        tdata1 = fits.getdata("%s/%s"%(srcFitDir, tname)) #first image is template
                        if tCmbImg.shape[0]==0:
                            tCmbImg=tdata1.copy()
                            regWid = int(tCmbImg.shape[1]/2)
                            regHei = int(tCmbImg.shape[0]/2)
                        imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid])
                    imgArray = np.array(imgs)
                    tCmbImg[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid] = np.median(imgArray,axis=0)
            
            tCmbImg = tCmbImg.astype(np.uint16) #np.int32
            outImgName = "%s_cmb%03d"%(tfiles[i*cmbNum+1].split('.')[0], imgArray.shape[0])
            fits.writeto("%s/%s.fit"%(destFitDir, outImgName), tCmbImg)
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            print("sim: %s use %d seconds"%(tfiles[i*cmbNum+1], runTime))
            #break
            
    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
            
def batchCombine():
    
    try:
        '''        
        srcFitDir1 = '/data/gwac_diff_xy/data/190101/remap'
        destFitDir1 = '/data/gwac_diff_xy/data/190101/comb'
        srcFitDir2 = '/data/gwac_diff_xy/data/190113/remap'
        destFitDir2 = '/data/gwac_diff_xy/data/190113/comb'
        srcFitDir3 = '/data/gwac_diff_xy/data/190117/remap'
        destFitDir3 = '/data/gwac_diff_xy/data/190117/comb'
                    
        superCombine(srcFitDir1, destFitDir1, cmbNum = -1)
        superCombine(srcFitDir2, destFitDir2, cmbNum = -1)
        superCombine(srcFitDir3, destFitDir3, cmbNum = -1)
        '''
        srcFitDir1 = '/data/gwac_diff_xy/data/190115/remap'
        destFitDir1 = '/data/gwac_diff_xy/data/190115/comb'
        srcFitDir2 = '/data/gwac_diff_xy/data/190116/remap'
        destFitDir2 = '/data/gwac_diff_xy/data/190116/comb'
                    
        superCombine(srcFitDir1, destFitDir1, cmbNum = -1)
        superCombine(srcFitDir2, destFitDir2, cmbNum = -1)

    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
     
            
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python SuperCombine2.py &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python SuperCombine2.py
if __name__ == "__main__":
    
    batchCombine()