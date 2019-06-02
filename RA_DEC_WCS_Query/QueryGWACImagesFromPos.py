# -*- coding: utf-8 -*-
import os
from astrotools import AstroTools
from astropy.wcs import WCS
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import traceback
import scipy.ndimage
import math
from astropy.io import fits
from gwac_util import zscale_image
from PIL import Image

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class QueryData:
    
    connParam={
        "host": "190.168.1.27",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    connParam2={
        "host": "172.28.8.28",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    connParam3={
        "host": "10.0.3.62",
        "port": "5433",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    
    def __init__(self):
        
        self.conn = False
        self.conn2 = False
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def query(self, sql):
        
        #print(sql)
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            self.closeDb()
        except Exception as err:
            rows = []
            print(" query OT2 image error ")
            print(err)
            
        return rows

def reAstrometry(tools, tpath, fname, x, y, ra0, dec0, otName):
    
    runSuccess = True
    workPath = 'twork'
    objName = 'reAstroObj.fit'
    
    imgpre= fname.split(".")[0]
    oImgf = "%s/%s.fit"%(tpath,imgpre)
    oImgfz = "%s/%s.fit.fz"%(tpath,imgpre)
    
    os.system("rm -rf %s"%(workPath))
    if not os.path.exists(workPath):
        os.system("mkdir -p %s"%(workPath))
    
    fileExist = True
    if os.path.exists(oImgf):
        os.system("cp %s %s/%s"%(oImgf, workPath, objName))
    elif os.path.exists(oImgfz):
        os.system("cp %s %s/%s.fz"%(oImgfz, workPath, objName))
        os.system("%s %s/%s.fz"%(tools.funpackProgram, workPath, objName))
    else:
        tools.log.warning("%s not exist"%(oImgf))
        fileExist = False
        runSuccess = False
    
    if fileExist:
        fieldId, cra,cdec = tools.removeHeaderAndOverScan(workPath, objName)
        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        tmplCat = tools.runSextractor(objName, workPath, workPath, fpar, sexConf, cmdStatus=0)
        
        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
        tmplCat = tools.runSextractor(objName, workPath, workPath, fpar, sexConf, cmdStatus=0, outSuffix='_ldac.fit')
        
        tools.ldac2fits('%s/%s'%(workPath,tmplCat), '%s/ti_cat.fit'%(workPath))
        
        ccdName = fname[:4]
        runSuccess = tools.runWCSRemotePC780(workPath,'ti_cat.fit', cra, cdec, ccdName)
        
        if runSuccess:
            wcs = WCS('%s/ti_cat.wcs'%(workPath))
            ra_center, dec_center = wcs.all_pix2world(4096/2, 4136/2, 1) #4136, 4096
            ot2ReRa, ot2ReDec = wcs.all_pix2world(x, y, 1)
            print('read_ra_center:%.5f, read_dec_center:%.5f, real_ra_center:%.5f, real_dec_center:%.5f'%(cra, cdec, ra_center, dec_center))
            print('%s, ra0:%.7f, dec0:%.7f, ot2ReRa:%.7f, ot2ReDec:%.7f, radiff:%.2farcsec, decdiff:%.2farcsec'%(otName, ra0, dec0, ot2ReRa, ot2ReDec, (ra0-ot2ReRa)*3600, (dec0-ot2ReDec)*3600))
        else:
            print('%s, get wcs error'%(fname))
            ot2ReRa, ot2ReDec = 0, 0
    
    return runSuccess, ot2ReRa, ot2ReDec

def posJudge(tools, tpath, fname, ra, dec, imgW=4096, imgH=4136):
    
    imgX, imgY = 0, 0
    isIn = False
    runSuccess = True
    workPath = 'twork'
    objName = 'reAstroObj.fit'
    
    imgpre= fname.split(".")[0]
    oImgf = "%s/%s.fit"%(tpath,imgpre)
    oImgfz = "%s/%s.fit.fz"%(tpath,imgpre)
    
    os.system("rm -rf %s"%(workPath))
    if not os.path.exists(workPath):
        os.system("mkdir -p %s"%(workPath))
    
    fileExist = True
    if os.path.exists(oImgf):
        os.system("cp %s %s/%s"%(oImgf, workPath, objName))
    elif os.path.exists(oImgfz):
        os.system("cp %s %s/%s.fz"%(oImgfz, workPath, objName))
        os.system("%s %s/%s.fz"%(tools.funpackProgram, workPath, objName))
    else:
        tools.log.warning("%s not exist"%(oImgf))
        fileExist = False
        runSuccess = False
    
    if fileExist:
        fieldId, cra,cdec = tools.removeHeaderAndOverScan(workPath, objName)
        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        tmplCat = tools.runSextractor(objName, workPath, workPath, fpar, sexConf, cmdStatus=0)
        
        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
        tmplCat = tools.runSextractor(objName, workPath, workPath, fpar, sexConf, cmdStatus=0, outSuffix='_ldac.fit')
        
        tools.ldac2fits('%s/%s'%(workPath,tmplCat), '%s/ti_cat.fit'%(workPath))
        
        ccdName = "%s_posjudge"%(fname[:4])
        runSuccess = tools.runWCSRemotePC780(workPath,'ti_cat.fit', cra, cdec, ccdName)
        
        if runSuccess:
            wcs = WCS('%s/ti_cat.wcs'%(workPath))
            
            try:
                imgX, imgY = wcs.all_world2pix(ra, dec, 1) #4136, 4096
                #print("imgX=%d(%d),imgY=%d(%d)"%(imgX, imgW, imgY, imgH))
                if imgX>0 and imgX<imgW and imgY>0 and imgY<imgH:
                    isIn = True
            except Exception as e:
                print(str(e))
                tstr = traceback.format_exc()
                print(tstr)

    return isIn, imgX, imgY

def getSkyList(tools, otName, ra, dec, startDate, endDate):
    
    sql1 = 'select sky_id, date_str, cam_id, count(*) ' \
        'from( ' \
        'select ff2.sky_id, ff2.cam_id, substr(ff2.img_path, 17, 6) as date_str ' \
        'from fits_file2_his ff2 ' \
        'WHERE ff2.gen_time>\'%s 07:00:00\' and ff2.gen_time<\'%s 23:59:59\' ' \
        'and ff2.sky_id in ( select sky1.sky_id from observation_sky sky1 INNER JOIN observation_sky sky2 on sky1.sky_name=sky2.sky_name ' \
        'INNER JOIN ot_level2_his ot2 on ot2.name=\'%s\' and ot2.sky_id=sky2.sky_id ' \
        ')) as tmpl ' \
        'GROUP BY sky_id, date_str, cam_id ' \
        'ORDER BY sky_id, date_str, cam_id'%(startDate, endDate, otName)
        
    tquery = QueryData()
    skyList = tquery.query(sql1)
    
    storePath = '/data/gwac_data/gwac_orig_fits'
    sql2 = "select img_name, img_path FROM " \
            "fits_file2_his WHERE sky_id=%d and cam_id=%d and substr(img_path, 17, 6)='%s' order by img_name"
    
    skyListFile = '%s_skyList.txt'%(otName)
    tf = open(skyListFile,'w')
    for i, tsky in enumerate(skyList):
        print(tsky)
        sky_id, date_str, cam_id, tnumber = tsky
        tsql = sql2%(sky_id, cam_id, date_str)
        fileList = tquery.query(tsql)
        fileNum = int(len(fileList)/2)
        selFile = fileList[fileNum]
        
        mountNum = int(cam_id/5) + 1
        ccdNum = cam_id%5
        if ccdNum>0:
            fname =selFile[0]
            print("select %s"%(fname))
            camName = '0%d%d'%(mountNum, ccdNum)
            tpath1 = '%s/%s/G00%d_%s'%(storePath, date_str, mountNum,camName)
            #print(tpath1)
            #print(fname)
            isIn, imgX, imgY = posJudge(tools, tpath1, fname, ra, dec)
            print("%s %d %s isIn:%s %.2f %.2f %s"%(date_str, sky_id, camName, isIn, imgX, imgY, fname))
            if isIn:
                tf.write("%s,%d,%d,%.2f,%.2f,%s\n"%(date_str, sky_id, cam_id, imgX, imgY, fname))
                tf.flush()
        #if i>10:
        #    break
    tf.close()
    
    return skyListFile

def getWindowImg(img, ctrPos, size):
    
    imgSize = img.shape
    hsize = int(size/2)
    tpad = int(size%2)
    ctrX = math.ceil(ctrPos[0])
    ctrY = math.ceil(ctrPos[1])
    
    minx = int(ctrX - hsize)
    maxx = int(ctrX + hsize + tpad)
    miny = int(ctrY - hsize)
    maxy = int(ctrY + hsize + tpad)
    
    widImg = []
    if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
        widImg=img[miny:maxy,minx:maxx]
        
    return widImg

def getWindowImgs(srcDir, objImg, x, y, size):
    
    objPath = "%s/%s"%(srcDir, objImg)
    objPathz = "%s/%s.fz"%(srcDir, objImg)
    
    if os.path.exists(objPath):
        objData = fits.getdata(objPath)
    elif os.path.exists(objPathz):
        objData = fits.getdata(objPathz)
        
    objWid = getWindowImg(objData, (x, y), size)
    return objWid

def getSubImages(skyListFile, otName):
    
    workPath = 'twork/%s'%(otName)
    os.system("rm -rf %s"%(workPath))
    if not os.path.exists(workPath):
        os.system("mkdir -p %s"%(workPath))
        
    size = 100
    storePath = '/data/gwac_data/gwac_orig_fits'
    skyList = np.loadtxt(skyListFile, dtype='str', delimiter=',')
    
    for tsky in skyList:
        #190208,2568,19,3365.45,3507.93,G044_mon_objt_190208T12320486.fit
        #print(tsky)
        dateStr = tsky[0]
        cam_id = int(tsky[2])
        mountNum = int(cam_id/5) + 1
        ccdNum = cam_id%5
        camName = '0%d%d'%(mountNum, ccdNum)
        tpath1 = '%s/%s/G00%d_%s'%(storePath, dateStr, mountNum,camName)
        fname =tsky[5]
        x =float(tsky[3])+20
        y =float(tsky[4])
        
        print("%s/%s"%(tpath1,fname))
        
        subImg = getWindowImgs(tpath1, fname, x, y, size)
        subImgz = zscale_image(subImg)
        subImgz = scipy.ndimage.zoom(subImgz, 4, order=0)
        
        imgpre= fname.split(".")[0]
        tImgName = "%s.jpg"%(imgpre)
        savePath = "%s/%s"%(workPath, tImgName)
        Image.fromarray(subImgz).save(savePath)

if __name__ == "__main__":
        
    toolPath = '/data/work/program/image_diff'
    tools = AstroTools(toolPath)
    
    tpath = '/data3/G004_044_190305'
    fname = 'G044_mon_objt_190305T13393793.fit'
    x = 3340.1064	
    y = 3500.967
    ra0 = 109.57737
    dec0 = 21.83166
    otName = 'G190305_D00383'
    
    #runSuccess, ot2ReRa, ot2ReDec = reAstrometry(tools, tpath, fname, x, y, ra0, dec0, otName)
    
    startDate = '2019-02-05' 
    endDate = '2019-05-05'
    #skyListFile = getSkyList(tools, otName, ra0, dec0, startDate, endDate)
    
    skyListFile ='G190305_D00383_skyList.txt'
    getSubImages(skyListFile, otName)