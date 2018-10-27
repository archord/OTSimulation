# -*- coding: utf-8 -*-
import os
from PIL import Image
from gwac_util import getFullAndSubThumbnail

def batch(srcPath, destPath, dateDirs):
    
    tempName = 'G043_mon_objt_181025T12592921.fit.fz'
    tempNameLen = len(tempName)
    for tdateStr in dateDirs:
        spath1 = "%s/%s"%(srcPath, tdateStr)
        dpath1 = "%s/20%s"%(destPath, tdateStr)
        if not os.path.exists(dpath1):
            os.system("mkdir %s"%(dpath1))
        
        ccdDirs = os.listdir(spath1)
        ccdDirs.sort()
        for tccd in ccdDirs:
            tccdName = tccd[0] + tccd[5:8]
            spath2 = "%s/%s"%(spath1, tccd)
            dpath2 = "%s/%s"%(dpath1, tccdName)
            if not os.path.exists(dpath2):
                os.system("mkdir %s"%(dpath2))
            
            fzimgs = os.listdir(spath2)
            fzimgs.sort()
            for timg in fzimgs:
                if len(timg)==tempNameLen:
                    imgName = timg.split(".")[0]
                    spath3 = "%s/%s"%(spath2, timg)
                    print(spath3)
                    dpath31 = "%s/%s.jpg"%(dpath2, imgName)
                    dpath32 = "%s/%s_min.jpg"%(dpath2, imgName)
                    fullImg, subImg = getFullAndSubThumbnail(spath2, timg)
                    Image.fromarray(fullImg).save(dpath31)
                    Image.fromarray(subImg).save(dpath32)
                    
                    break
            break
        break
        
if __name__ == "__main__":
    
    srcPath = "/data/gwac_data/gwac_orig_fits"
    destPath = "/data/gwac_data/thumbnail"
    dateDirs = ['181025','181024','181023','181022']
    batch(srcPath, destPath, dateDirs)
    