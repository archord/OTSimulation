# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime
import traceback
from astropy.io import fits
import math

def superCombine(srcFitDir, destFitDir):

    try:
        if not os.path.exists(destFitDir):
            os.system("mkdir -p %s"%(destFitDir))
            
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            if tfile[-8:]=='conv.fit':
                tfiles.append(tfile)
        
        #tnum = len(tfiles)-1
        tnum = len(tfiles)
        print("total cmb %d"%(tnum))
            
        starttime = datetime.now()
        tCmbImg = np.array([])
        
        imgs = []
        for j in range(0,tnum):
            tname = tfiles[j]
            print("read %d, %s"%(j, tname))
            tdata1 = fits.getdata("%s/%s"%(srcFitDir, tname))
            #tdata1=tdata1.astype(np.float32)
            imgs.append(tdata1)
        imgArray = np.array(imgs)
        tCmbImg = np.median(imgArray,axis=0)
        
        tCmbImg = tCmbImg.astype(np.uint16) #np.int32
        outImgName = "%s_cmb%03d"%(tfiles[0].split('.')[0], imgArray.shape[0])
        fits.writeto("%s/%s.fit"%(destFitDir, outImgName), tCmbImg)
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        print("sim: %s use %d seconds"%(tfiles[0], runTime))        
    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
            
def batchCombine():
    
    try:
        srcFitDir1 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/190101_G004_041_rst/data/20191107_p1/G_diffImg'
        destFitDir1 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/cmb'
        srcFitDir2 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/190113_G004_041_rst/data/20191107_p1/G_diffImg'
        destFitDir2 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/cmb'
                    
        superCombine(srcFitDir1, destFitDir1)
        superCombine(srcFitDir2, destFitDir2)

    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
     
            
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python SuperCombine2.py &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python SuperCombine2.py
if __name__ == "__main__":
    
    batchCombine()