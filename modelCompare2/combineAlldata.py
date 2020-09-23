# -*- coding: utf-8 -*-
import os
import numpy as np


def combineData(rootPath, destPath):
    
    imgs0 = np.array([])
    parms0 = np.array([])
    obsUtc0 = []
    
    tdirs =  os.listdir(rootPath)
    for tdir in tdirs:
        tpath0 = "%s/%s"%(rootPath, tdir)
        tfiles = os.listdir(tpath0)
        print("load dir %s, has %d files."%(tpath0, len(tfiles)))
        for tfile in tfiles:
            tpath1 = "%s/%s"%(tpath0, tfile)
            tdata = np.load(tpath1)
            imgs = tdata['imgs']
            parms = tdata['parms']
            obsUtc = tdata['obsUtc']
            
            obsUtc0.append(obsUtc)
            if imgs0.shape[0]==0:
                imgs0 = imgs
                parms0 = parms
            else:
                imgs0 = np.concatenate((imgs0, imgs), axis=0)
                parms0 = np.concatenate((parms0, parms), axis=0)
                
    obsUtc0 = np.array(obsUtc0)
    print("total combined image %d"%(imgs0.shape[0]))
    
    np.savez_compressed(destPath, imgs=imgs0, parms=parms0, obsUtc=obsUtc0)
    
if __name__ == "__main__":
    
    rootPath = "/home/xy/Downloads/myresource/deep_data2/simot/minorPlanet20200202/minorplanetStamp/J_subImg_mpimgt"
    destPath = "/home/xy/Downloads/myresource/deep_data2/simot/minorPlanet20200202/minorplanetStamp.npz"
    
    combineData(rootPath, destPath)