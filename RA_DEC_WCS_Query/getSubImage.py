# -*- coding: utf-8 -*-
from astropy.io import fits

def getWindowImgs(srcDir, objImg):
    
    objPath = "%s/%s"%(srcDir, objImg)
    objData = fits.getdata(objPath)
    
    #1266,234
    minx = 400
    maxx = 800
    miny = 400
    maxy = 800
    widImg=objData[miny:maxy,minx:maxx]
    
    newPath = "%s/%s_sub400.fit"%(srcDir, objImg.split('.')[0])
    hdu = fits.PrimaryHDU(widImg)
    hdul = fits.HDUList([hdu])
    hdul.writeto(newPath)


if __name__ == "__main__":
    '''
    storePath = '/home/xy/test7'
    tfile1 ='G031_mon_objt_190115T21195318_align.fit'
    tfile2 ='G041_mon_objt_190101T21511991_align.fit'
    tfile3 ='G041_mon_objt_190117T22015711_align.fit'
    tfile4 ='G031_mon_objt_190116T21321726_align.fit'
    tfile5 ='G041_mon_objt_190113T21571311_align.fit'
    
    getWindowImgs(storePath, tfile1)
    getWindowImgs(storePath, tfile2)
    getWindowImgs(storePath, tfile3)
    getWindowImgs(storePath, tfile4)
    getWindowImgs(storePath, tfile5)
    '''
    
    storePath = '/home/xy/test4'
    tfile1 ='G021_Mon_objt_190603T13294896.fit'
    tfile2 ='G021_Mon_objt_190603T13301896.fit'
    
    getWindowImgs(storePath, tfile1)
    getWindowImgs(storePath, tfile2)
    