# -*- coding: utf-8 -*-
from astropy.io import fits
import os

def removeHeader(fname):
    
    tmpDir = r"E:\test2"
    fullPath = "%s/%s"%(tmpDir, fname)
    
    keyword=['BZERO']

    with fits.open(fullPath, mode='update') as hdul:
        hdr = hdul[0].header
        #print(hdr)
        #DATEOBS = hdr["DATE-OBS"]
        #print(DATEOBS)
        #hdr["DATE-OBS"]=DATEOBS[:-4]
        #hdr["DATE-OBS"]="2018-11-12T21:45:02.123"
        for kw in keyword:
            hdr.remove(kw,ignore_missing=True)
        hdul.flush()
        hdul.close()
            
if __name__ == "__main__":
    
    fname = "G181112_C15849_R_181112_00001.fit.fz"
    removeHeader(fname)