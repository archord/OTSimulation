# -*- coding: utf-8 -*-
from astrotools import AstroTools
from astropy.wcs import WCS

def getImgCenter(tpath, imgName, x, y):
    
    tools = AstroTools('/home/xy/Downloads/myresource/deep_data2/image_diff')
    fieldId, ra,dec = tools.getRaDec(tpath, imgName)
    fpar='sex_diff.par'
    sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
    tmplCat, isSuccess = tools.runSextractor(imgName, tpath, tpath, fpar, sexConf, outSuffix='_ldac.fit')
    if not isSuccess:
        print("getDiffTemplate runSextractor failure2")
        return isSuccess, 0,0
    
    tools.ldac2fits('%s/%s'%(tpath,tmplCat), '%s/ti_cat.fit'%(tpath))
    
    runSuccess = tools.runWCS(tpath,'ti_cat.fit', ra, dec)
    
    if runSuccess:
        wcs = WCS('%s/ti_cat.wcs'%(tpath))
        ra, dec = wcs.all_pix2world(x, y, 1)
            
    return runSuccess, ra, dec


if __name__ == "__main__":
    
    tpath = '/home/xy/work/astroTest'
    imgName = 'G021_Mon_objt_191128T10112517.fit'
    x=1441.6107
    y=2144.8833
    
    runSuccess, ra, dec = getImgCenter(tpath, imgName, x, y)
    if runSuccess:
        print('ra=%f,dec=%f'%(ra,dec))