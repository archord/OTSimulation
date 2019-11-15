# -*- coding: utf-8 -*-
from astropy.io import fits

def changeHeader(srcDir, objImg, zoom=3):
    
    objPath = "%s/%s"%(srcDir, objImg)
    objData, theader = fits.getdata(objPath, header=True)
    '''
    theader['BITPIX']=-32
    theader['BSCALE']=1.0
    theader['BZERO']=0.0
    
    newPath = "%s/%s_2.fit"%(srcDir, objImg.split('.')[0])
    fits.writeto(newPath, objData, header=theader, overwrite=True)
    '''
    newPath = "%s/%s_3.fit"%(srcDir, objImg.split('.')[0])
    hdu = fits.PrimaryHDU(objData)
    hdul = fits.HDUList([hdu])
    hdul.writeto(newPath)

if __name__ == "__main__":
    
    storePath = r'G:\SuperNova20190113\stampImage\test3'
    tfile1 ='G041_mon_objt_190113T22252817_s800_bkg2.fit'
    
    changeHeader(storePath, tfile1)
    