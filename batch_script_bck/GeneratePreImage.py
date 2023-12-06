# -*- coding: utf-8 -*-
import os
from PIL import Image
from gwac_util import getFullAndSubThumbnail

def batch(srcPath, destPath):

    tempName = 'G043_mon_objt_181025T12592921.fit.fz'
    tempNameLen = len(tempName)
    
    dateDirs = os.listdir(srcPath)
    dateDirs.sort(reverse=True)
    for tdateStr in dateDirs:
        spath1 = "%s/%s"%(srcPath, tdateStr)
        dpath1 = "%s/%s"%(destPath, tdateStr)
        if not os.path.exists(dpath1):
            os.system("mkdir %s"%(dpath1))
        
        print(tdateStr)
        ccdDirs = os.listdir(spath1)
        ccdDirs.sort(reverse=True)
        for tccd in ccdDirs:
            tccdName = tccd[0] + tccd[5:8]
            spath2 = "%s/%s"%(spath1, tccd)
            dpath2 = "%s/%s"%(dpath1, tccdName)
            if not os.path.exists(dpath2):
                os.system("mkdir %s"%(dpath2))
            
            print(tccd)
            fzimgs = os.listdir(spath2)
            fzimgs.sort()
            fzimgs2 = []
            for timg in fzimgs:
                if len(timg)==tempNameLen:
                    fzimgs2.append(timg)
            
            for ii, timg in enumerate(fzimgs2):
                if ii%10==1:
                    imgName = timg.split(".")[0]
                    #spath3 = "%s/%s"%(spath2, timg)
                    #dpath31 = "%s/%s.jpg"%(dpath2, imgName)
                    dpath32 = "%s/%s_min.jpg"%(dpath2, imgName)
                    fullImg, subImg = getFullAndSubThumbnail(spath2, timg)
                    #Image.fromarray(fullImg).save(dpath31)
                    Image.fromarray(subImg).save(dpath32,optimize=True,quality=30)

                    #break
            #break
        #break
        
if __name__ == "__main__":
    
    srcPath = "/data/gwac_data/gwac_orig_fits"
    destPath = "/data/gwac_data/thumbnail"
    batch(srcPath, destPath)
    '''
    tquality=30
    tpath = "E:/test"
    fname = "G020_mon_objt_170927T15530278.fit.fz"
    fullImg, subImg = getFullAndSubThumbnail(tpath, fname)
    Image.fromarray(subImg).save("E:/test/ac%d.jpg"%(tquality),optimize=True,quality=tquality)
    '''
