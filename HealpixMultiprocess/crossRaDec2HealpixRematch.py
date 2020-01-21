# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import multiprocessing
import pandas as pd
from astropy_healpix import HEALPix
from astropy import units as u
import traceback

def getGreatCircleDistance(ra1, dec1, ra2, dec2):
    rst = 57.295779513 * math.acos(math.sin(0.017453293 * dec1) * math.sin(0.017453293 * dec2)
            + math.cos(0.017453293 * dec1) * math.cos(0.017453293 * dec2) * math.cos(0.017453293 * (math.fabs(ra1 - ra2))));
    return rst    

def getIdx(tdata, hp):
    
    tdata2=[]
    for td in tdata:
        tdata2.append([td[1],td[2]])
    tdata = np.array(tdata2)
    ra = tdata[:,0]
    dec = tdata[:,1]
    
    hpix = hp.lonlat_to_healpix(ra * u.deg, dec * u.deg)
    tidx = []
    for i in range(hp.npix):
        tidx.append([])
    j=0
    for tpix in hpix:
        tidx[tpix].append((ra[j],dec[j],j))
        j=j+1
    
    return tidx
    
        
def tmatch():
    
    maxDist = 3.0/60/60
    hp = HEALPix(nside=512)
    
    tpath = '/data/work/hjtian/QSOs_NINA.txt'
    tdata00=np.loadtxt(tpath,dtype='str') #, delimiter=' '
    print(tdata00.shape)
    raDec00=tdata00[:,0:2].astype(np.float)
    tdata00Match = []
    for i in range(raDec00.shape[0]):
        tdata00Match.append([])
    
    root = '/data/work/hjtian/crossmatch20200118'
    destDir = '/data/work/hjtian/crossmatch20200120Rematch'
    if not os.path.exists(destDir):
        os.system("mkdir -p %s"%(destDir))
      
    dirs = os.listdir(root)
    tdata = np.array([])
    for iii, tdir in enumerate(dirs):
        
        tdataPath = "%s/%s"%(root,tdir)
        print(tdataPath)
        tds = pd.read_csv(tdataPath).to_numpy()
        if tdata.shape[0]==0:
            tdata=tds
        elif tdata.shape[0]>0:
            tdata = np.concatenate([tdata, tds])
    
    print(tdata.shape)
    tidxHealpix = getIdx(tdata, hp)

    try:
        for i in range(raDec00.shape[0]):
            ra00 = raDec00[i,0]
            dec00 = raDec00[i,1]
            if i%100000==0:
                print(i)
            hpixs = hp.cone_search_lonlat(ra00 * u.deg, dec00 * u.deg, radius=maxDist * u.deg)
            minDist=maxDist
            tmchIdx = -1
            for ti in hpixs:
                tposs = tidxHealpix[ti]
                for tpos in tposs:
                    ra2=tpos[0]
                    dec2=tpos[1]

                    tdist = getGreatCircleDistance(ra00, dec00, ra2, dec2)
                    if tdist<=minDist:
                        #print("ra1=%f,dec1=%f, ra2=%f,dec2=%f, tdist=%f, maxDist=%f"%(ra00,dec00, ra2,dec2, tdist, maxDist))
                        minDist = tdist
                        tmchIdx = tpos[2]
            if tmchIdx>-1:
                if len(tdata00Match[i])>0:
                    if tdata00Match[i][0]>minDist:
                        tm=tdata00Match[i][0]
                        tm[0]=minDist
                        tm[1]=tdata[tmchIdx]
                        #tdata00Match[i].append([minDist,tdata[tmchIdx]])
                else:
                    tdata00Match[i].append([minDist,tdata[tmchIdx]])
                #break

    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
    #break
    
    rst1 = []
    rst2 = []
    for i in range(len(tdata00Match)):
        if len(tdata00Match[i])>0:
            #print(tdata00Match[i])
            rst1.append(tdata00[i])
            rst2.append(tdata00Match[i][0][1])
    if len(rst1)>0:
        
        destDir = '/data/work/hjtian/crossmatch20200120all'
        if not os.path.exists(destDir):
            os.system("mkdir -p %s"%(destDir))
        savePath = '%s/data1_%d.csv'%(destDir,len(rst1))
        print(savePath)
        GPS1_df = pd.DataFrame(rst1)
        GPS1_df.to_csv(savePath, index=False)
        
        savePath = '%s/data2_%d.csv'%(destDir,len(rst2))
        print(savePath)
        GPS1_df = pd.DataFrame(rst2)
        GPS1_df.to_csv(savePath, index=False)

if __name__ == "__main__":
    
    tmatch()
    
    