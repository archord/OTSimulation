# -*- coding: utf-8 -*-
from astropy.io import fits
import scipy.ndimage

def zoomImage(srcDir, objImg, zoom=3):
    
    objPath = "%s/%s"%(srcDir, objImg)
    objData = fits.getdata(objPath)
    objData = scipy.ndimage.zoom(objData, zoom, order=0)
    
    newPath = "%s/%s_zoom%d.fit"%(srcDir, objImg.split('.')[0], zoom)
    hdu = fits.PrimaryHDU(objData)
    hdul = fits.HDUList([hdu])
    hdul.writeto(newPath)


if __name__ == "__main__":
    
    storePath = r'G:\SuperNova20190113\stampImage\190101_G004_041_test'
    tfile1 ='G041_mon_objt_190113T21105811_s800.fit'
    tfile2 ='G041_mon_objt_190113T22252817_s800.fit'
    
    zoomImage(storePath, tfile1)
    zoomImage(storePath, tfile2)
    