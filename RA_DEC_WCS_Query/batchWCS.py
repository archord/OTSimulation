# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime
import traceback
import psycopg2
import cv2
from astropy.wcs import WCS
from astrotools import AstroTools
from astropy.io import fits
import math

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
            
class BatchImageDiff(object):
    def __init__(self, dataRoot, dataDest, tools, camName, skyName): 
        
        self.camName = camName
        self.skyName = str(skyName)
        self.ffNumber = 0
        self.toolPath = os.getcwd()
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        
        #self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s"%(dataRoot)
        self.srcDir = "%s"%(dataRoot)
        
        self.catDir="%s/cat"%(dataDest)
        self.wcsDir="%s/wcs"%(dataDest)
        self.remapDir="%s/remap"%(dataDest)
            
        self.objectImg = 'oi.fit'
        self.templateImg = 'ti.fit'
        self.objectImgSim = 'ois.fit'
        self.objTmpResi = 'otr.fit'
        self.simTmpResi = 'str.fit'
        self.newImageName = "new.fit"
        
        self.badPixCat = 'badpix.cat'
        self.objectImgSimAdd = 'oisa.cat'
        self.objectImgCat = 'oi.cat'
        self.templateImgCat = 'ti.cat'
        self.objectImgSimCat = 'ois.cat'
        self.objTmpResiCat = 'otr.cat'
        self.simTmpResiCat = 'str.cat'
        
        self.imgSize = (4136, 4096)
        self.subImgSize = 21
        self.imgShape = []  
             
        self.selTemplateNum = 20 # 10 3
        self.maxFalseNum = 5
        
        self.tools = tools
        self.log = tools.log
        #self.modelName='model_128_5_RealFOT_8_190111.h5'
        #self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.modelName='model_80w_20190403_branch3_train12_79.h5'
        
        self.initReg(0)
                
        if not os.path.exists(self.wcsDir):
            os.system("mkdir -p %s"%(self.wcsDir))
        if not os.path.exists(self.remapDir):
            os.system("mkdir -p %s"%(self.remapDir))

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s, sky:%s, ffNum:%d\n %s"%(self.camName, self.skyName, self.ffNumber, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
            if not os.path.exists(self.tmpUpload):
                os.system("mkdir -p %s"%(self.tmpUpload))
            if not os.path.exists(self.templateDir):
                os.system("mkdir -p %s"%(self.templateDir))
            if not os.path.exists(self.tmpDir):
                os.system("mkdir -p %s"%(self.tmpDir))
            if not os.path.exists(self.tmpCat):
                os.system("mkdir -p %s"%(self.tmpCat))
        
        self.procNum = 0
        self.tmplImgIdx = 0 
        self.regFalseNum = 0
        self.regSuccessNum = 0
        self.diffFalseNum = 0
        self.origTmplImgName = ""
        self.regFalseIdx = 0
        self.makeTempFalseNum = 0
        self.imglist = []
        self.transHGs = []
    
    def getWCS(self, srcDir, imgName, ra0=-1000, dec0=-1000):
        
        starttime = datetime.now()
        
        os.system("rm -rf %s/*"%(self.tmpDir))
        
        imgpre= imgName.split(".")[0]
        oImgf = "%s/%s.fit"%(srcDir,imgpre)
        oImgfz = "%s/%s.fit.fz"%(srcDir,imgpre)
        if os.path.exists(oImgf):
            os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, self.tmpDir, self.objectImg))
        elif os.path.exists(oImgfz):
            os.system("cp %s/%s.fit.fz %s/%s.fz"%(srcDir, imgpre, self.tmpDir, self.objectImg))
            os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
        else:
            self.log.warning("%s not exist"%(oImgf))
            return False
                
        fieldId, cra,cdec = self.tools.removeHeaderAndOverScan(self.tmpDir,self.objectImg)

        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
        tmplCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf, cmdStatus=0, outSuffix='_ldac.fit')
        self.tools.ldac2fits('%s/%s'%(self.tmpDir,tmplCat), '%s/ti_cat.fit'%(self.tmpDir))
        
        if ra0<360 and ra0>0 and dec0>-90 and dec0<90:
            cra, cdec = ra0, dec0
        runSuccess = self.tools.runWCS(self.tmpDir,'ti_cat.fit', cra, cdec)
        
        wcsfile = 'ti_cat.wcs'
        if runSuccess:
            wcs = WCS('%s/%s'%(self.tmpDir, wcsfile))
            #ra_center, dec_center = wcs.all_pix2world(4096/2, 4136/2, 1) #4136, 4096
            ra_center, dec_center = wcs.all_pix2world(self.imgSize[1]/2, self.imgSize[0]/2, 1)
            print('%s, read_ra_center:%.5f, read_dec_center:%.5f, real_ra_center:%.5f, real_dec_center:%.5f'%(imgName, cra, cdec, ra_center, dec_center))
        else:
            print('%s, get wcs error'%(imgName))
            ra_center, dec_center = 0, 0
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** get WCS %s use %d seconds"%(imgName, runTime))
        print("********** get WCS %s use %d seconds"%(imgName, runTime))
        
        return wcsfile, ra_center, dec_center

    def getMatchPosHmg2(self, dataOi, dataTi):
        
        dataOi = dataOi.astype(np.float32)
        dataTi = dataTi.astype(np.float32)
        h, tmask = cv2.findHomography(dataOi, dataTi, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
        
        dataTi2 = cv2.perspectiveTransform(np.array([dataOi]), h)
        dataTi2 = dataTi2[0]
        
        tmean, trms, tmax, tmin = self.tools.evaluatePos(dataOi, dataTi2)
        tmean2, trms2, tmax2, tmin2 = self.tools.evaluatePos(dataTi, dataTi2, True)
        
        xshift = tmean[0]
        yshift = tmean[1]
        xrms = trms2[0]
        yrms = trms2[1]
        
        return h, xshift, yshift, xrms, yrms
    
    def reMapImg(self, objWCSFile, tmpWCS, fitsPath):
        
        objWCS = WCS('%s/%s'%(self.wcsDir, objWCSFile))
        coors = []
        for y in range(1,41):
            ty = y*100
            for x in range(1,41):
                tx = x*100
                coors.append([tx, ty])
        objXY = np.array(coors)
        objRaDec = objWCS.all_pix2world(objXY, 1)
        tmpXY = tmpWCS.all_world2pix(objRaDec, 1)
        
        h, xshift, yshift, xrms, yrms = self.getMatchPosHmg2(objXY, tmpXY)
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
        
        tname00 = "%s.fit"%(objWCSFile.split('.')[0])
        tpath = "%s/%s"%(fitsPath, tname00)
        tpathz = "%s/%s.fz"%(fitsPath, tname00)
        if os.path.exists(tpath):
            timgName = tname00
        elif os.path.exists(tpathz):
            timgName = tname00 + '.fz'
        else:
            print("%s not exist"%(tpath))
            return
        
        tpath = "%s/%s"%(fitsPath, timgName)
        tData = fits.getdata(tpath)
        #overscanLeft = 20
        #overscanRight = 80
        #overscanLeft = 50
        #overscanRight = 50
        #tData = tData[50:-tData.shape[0],overscanLeft:-overscanRight]
        #print(type(tData[0][0])) #numpy.uint16
        #tData = tData.astype(np.float32)
        newimage = cv2.warpPerspective(tData, h, (tData.shape[1],tData.shape[0]))
        print(newimage.shape)
        
        newName = "%s_align.fit"%(objWCSFile.split('.')[0])
        newPath = "%s/%s"%(fitsPath, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(newimage)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath, overwrite=True)
         
def run1(srcPath00,dateStr,camName, curSkyId):
    
    #toolPath = os.getcwd()
    toolPath = '/home/gwac/img_diff_xy/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "/data/gwac_diff_xy/data"
    logDest0 = "/data/gwac_diff_xy/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    startProcess = False
    dayRun = 0
    nigRun = 0
    skyId = 0
    ffId = 0
    tfiles = []
    #srcPath00='/data1/G004_041_190124'
    #dateStr='190124'
    #camName='G041'
    #curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(srcPath00, dstDir, tools, camName, curSkyId)

    try:
        camId = (int(camName[1])-1)*5 + int(camName[2])
        sql1 = "select img_name " \
            "from fits_file2_his " \
            "where sky_id=%s and cam_id=%s and substr(img_path, 17, 6)='%s'  " \
            "order by img_name"%(curSkyId, camId, dateStr)
        
        print(sql1)
        tquery = QueryData()
        tfiles = tquery.query(sql1)
        
        print("total has %d images"%(len(tfiles)))
        
        ra0, dec0 = -1000, -1000
        for i, tname in enumerate(tfiles):
            
            tname00 = tname[0]
            tpath = "%s/%s"%(srcPath00, tname00)
            tpathz = "%s/%s.fz"%(srcPath00, tname00)
            if os.path.exists(tpath):
                timgName = tname00
            elif os.path.exists(tpathz):
                timgName = tname00 + '.fz'
            else:
                print("%s not exist"%(tpath))
                continue
            tStr = "start diff: %s"%(timgName)
            tdiff.log.info(tStr)
            starttime = datetime.now()
            
            print("process %s"%(timgName))
            wcsfile, ra_center, dec_center = tdiff.getWCS(srcPath00, timgName, ra0, dec0)
            ra0, dec0 = ra_center, dec_center
            os.system("cp %s/%s %s/%s.wcs"%(tdiff.tmpDir, wcsfile, tdiff.wcsDir, timgName.split('.')[0]))
            
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            tdiff.log.info("totalTime %d seconds, %s"%(runTime, timgName))
                
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        try:
            if 'tdiff' in locals():
                tStr = "diff error"
                tdiff.log.info(tStr)
                tdiff.sendMsg(tStr)
        except Exception as e1:
            print(str(e1))
            tstr = traceback.format_exc()
            print(tstr)
    
def batchRunWCS():
    
    skyListFile = 'AT2019va_dateList.txt'
    
    #skyList = np.loadtxt(skyListFile, dtype='str', delimiter=',')
    skyList = np.loadtxt(skyListFile, dtype='str')
    
    for tsky in skyList:
        #190208,2568,19,3365.45,3507.93,G044_mon_objt_190208T12320486.fit
        #print(tsky)
        dateStr = tsky[0]
        skyId = int(tsky[1])
        camName = tsky[2]
        fname =tsky[5]
        tpath1 = tsky[7]
        
        print(tsky)
        if os.path.exists(tpath1):
            print("%s/%s"%(tpath1,fname))
            run1(tpath1,dateStr,camName, skyId)

def wcsAlign(srcPath00,dateStr,camName, curSkyId):
    
    #toolPath = os.getcwd()
    toolPath = '/data/work/program/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "/data/gwac_diff_xy/data"
    logDest0 = "/data/gwac_diff_xy/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    startProcess = False
    dayRun = 0
    nigRun = 0
    skyId = 0
    ffId = 0
    tfiles = []
    #srcPath00='/data1/G004_041_190124'
    #dateStr='190124'
    #camName='G041'
    #curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(srcPath00, dstDir, tools, camName, curSkyId)

    try:
        tfiles0 = os.listdir(tdiff.wcsDir)
        tfiles0.sort()
        
        print("total has %d images"%(len(tfiles0)))
        tmpWCSIdx = int(len(tfiles0)/2)
        tmpWCSFile = tfiles0[tmpWCSIdx]
        tmpWCS = WCS('%s/%s'%(tdiff.wcsDir, tmpWCSFile))
        print("select %d %s as tmp WCS"%(tmpWCSIdx, tmpWCSFile))
        
        for i, tname in enumerate(tfiles0):
            
            if i==tmpWCSIdx:
                tname00 = tname.split('.')[0] + '.fit'
                tpath = "%s/%s"%(srcPath00, tname00)
                tpathz = "%s/%s.fz"%(srcPath00, tname00)
                if os.path.exists(tpath):
                    timgName = tname00
                    os.system("cp %s/%s %s/%s.wcs"%(srcPath00, timgName, tdiff.remapDir, timgName))
                elif os.path.exists(tpathz):
                    timgName = tname00 + '.fz'
                    os.system("cp %s/%s %s/%s"%(srcPath00, timgName, tdiff.remapDir, timgName))
                    os.system("%s %s/%s"%(tools.funpackProgram, tdiff.remapDir, timgName))
                    os.system("rm -rf %s/%s"%(tdiff.remapDir, timgName))
                else:
                    print("%s not exist"%(tpath))
                    continue
            else:
                starttime = datetime.now()
                
                print("remap %s"%(tname))
                tdiff.reMapImg(tname, tmpWCS, srcPath00)
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                tdiff.log.info("totalTime %d seconds, %s"%(runTime, tname))
                
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        try:
            if 'tdiff' in locals():
                tStr = "diff error"
                tdiff.log.info(tStr)
                tdiff.sendMsg(tStr)
        except Exception as e1:
            print(str(e1))
            tstr = traceback.format_exc()
            print(tstr)
    
def batchAlign():
    
    skyListFile = 'AT2019va_dateList.txt'
    
    #skyList = np.loadtxt(skyListFile, dtype='str', delimiter=',')
    skyList = np.loadtxt(skyListFile, dtype='str')
    
    for tsky in skyList:
        #190208,2568,19,3365.45,3507.93,G044_mon_objt_190208T12320486.fit
        #print(tsky)
        dateStr = tsky[0]
        skyId = int(tsky[1])
        camName = tsky[2]
        fname =tsky[5]
        tpath1 = tsky[7]
        
        print(tsky)
        if os.path.exists(tpath1):
            print("%s/%s"%(tpath1,fname))
            wcsAlign(tpath1,dateStr,camName, skyId)

def superCombine(srcFitDir, destFitDir, cmbNum = 5, regions=[2,2]):

    try:
        destFitDir = "%s/%03d"%(destFitDir, cmbNum)
        if not os.path.exists(destFitDir):
            os.system("mkdir -p %s"%(destFitDir))
            
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            tfiles.append(tfile)
        
        #tnum = len(tfiles)-1
        tnum = len(tfiles)
        if cmbNum<0:
            cmbNum = tnum
        totalCmb = math.floor(tnum*1.0/cmbNum)
        print("total cmb %d"%(totalCmb))
        for i in range(totalCmb):
            
            starttime = datetime.now()
            tCmbImg = np.array([])
            regWid = 0
            regHei = 0
            for ty in range(regions[0]):
                for tx in range(regions[1]):
                    imgs = []
                    for j in range(0,cmbNum):
                        tIdx = i*cmbNum+j
                        #tIdx = tnum - (i*cmbNum+j)
                        if tIdx > tnum-1 or tIdx <0:
                            break
                        tname = tfiles[tIdx]
                        print("read %d, %s"%(tIdx, tname))
                        tdata1 = fits.getdata("%s/%s"%(srcFitDir, tname)) #first image is template
                        if tCmbImg.shape[0]==0:
                            tCmbImg=tdata1.copy()
                            regWid = int(tCmbImg.shape[1]/2)
                            regHei = int(tCmbImg.shape[0]/2)
                        imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid])
                    imgArray = np.array(imgs)
                    tCmbImg[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid] = np.median(imgArray,axis=0)
            
            tCmbImg = tCmbImg.astype(np.uint16) #np.int32
            outImgName = "%s_cmb%03d"%(tfiles[i*cmbNum+1].split('.')[0], imgArray.shape[0])
            fits.writeto("%s/%s.fit"%(destFitDir, outImgName), tCmbImg)
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            print("sim: %s use %d seconds"%(tfiles[i*cmbNum+1], runTime))
            #break
            
    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
            
def batchCombine():
    
    try:
        '''        
        srcFitDir1 = '/data/gwac_diff_xy/data/190101/remap'
        destFitDir1 = '/data/gwac_diff_xy/data/190101/comb'
        srcFitDir2 = '/data/gwac_diff_xy/data/190113/remap'
        destFitDir2 = '/data/gwac_diff_xy/data/190113/comb'
        srcFitDir3 = '/data/gwac_diff_xy/data/190117/remap'
        destFitDir3 = '/data/gwac_diff_xy/data/190117/comb'
                    
        superCombine(srcFitDir1, destFitDir1, cmbNum = -1)
        superCombine(srcFitDir2, destFitDir2, cmbNum = -1)
        superCombine(srcFitDir3, destFitDir3, cmbNum = -1)
        '''
        srcFitDir1 = '/data/gwac_diff_xy/data/190115/remap'
        destFitDir1 = '/data/gwac_diff_xy/data/190115/comb'
        srcFitDir2 = '/data/gwac_diff_xy/data/190116/remap'
        destFitDir2 = '/data/gwac_diff_xy/data/190116/comb'
                    
        superCombine(srcFitDir1, destFitDir1, cmbNum = -1)
        superCombine(srcFitDir2, destFitDir2, cmbNum = -1)

    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
            
def wcsRemap():
    
    #toolPath = os.getcwd()
    toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "tmp/data"
    logDest0 = "tmp/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    startProcess = False
    dayRun = 0
    nigRun = 0
    skyId = 0
    ffId = 0
    tfiles = []
    srcPath00='/home/xy/test7'
    dateStr='190124'
    camName='G041'
    curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(srcPath00, dstDir, tools, camName, curSkyId)

    try:
        
        tfiles0 = os.listdir(srcPath00)
        tfiles0.sort()
        
        ra0, dec0 = -1000, -1000
        for timgName in tfiles0:
            if timgName.find('fit')>0:
                wcsfile, ra_center, dec_center = tdiff.getWCS(srcPath00, timgName, ra0, dec0)
                ra0, dec0 = ra_center, dec_center
                print("%f, %f"%(ra0, dec0))
                os.system("cp %s/%s %s/%s.wcs"%(tdiff.tmpDir, wcsfile, srcPath00, timgName.split('.')[0]))
        
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        try:
            if 'tdiff' in locals():
                tStr = "diff error"
                tdiff.log.info(tStr)
                tdiff.sendMsg(tStr)
        except Exception as e1:
            print(str(e1))
            tstr = traceback.format_exc()
            print(tstr)
            
            
def wcsAlign2():
    
    #toolPath = os.getcwd()
    toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "tmp/data"
    logDest0 = "tmp/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    startProcess = False
    dayRun = 0
    nigRun = 0
    skyId = 0
    ffId = 0
    tfiles = []
    srcPath00='/home/xy/test7'
    dateStr='190124'
    camName='G041'
    curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(srcPath00, dstDir, tools, camName, curSkyId)
    tdiff.wcsDir = srcPath00

    try:
        tfiles0 = os.listdir(srcPath00)
        tfiles0.sort()
        
        tmpWCSFile = 'G031_mon_objt_190116T21321726.wcs'
        tmpWCS = WCS('%s/%s'%(tdiff.wcsDir, tmpWCSFile))
        print("select %s as tmp WCS"%(tmpWCSFile))
        
        for i, tname in enumerate(tfiles0):
            
            if tname.find('wcs')>0 and tname.find(tmpWCSFile.split('.')[0])<0:
                starttime = datetime.now()
                
                print("remap %s"%(tname))
                tdiff.reMapImg(tname, tmpWCS, srcPath00)
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                tdiff.log.info("totalTime %d seconds, %s"%(runTime, tname))
                
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        try:
            if 'tdiff' in locals():
                tStr = "diff error"
                tdiff.log.info(tStr)
                tdiff.sendMsg(tStr)
        except Exception as e1:
            print(str(e1))
            tstr = traceback.format_exc()
            print(tstr)
            
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    #batchRunWCS()
    #batchAlign()
    #batchCombine()
    #wcsRemap()
    wcsAlign2()