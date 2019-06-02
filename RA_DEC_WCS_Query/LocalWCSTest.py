# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime
import traceback
from astropy.wcs import WCS
from astrotools import AstroTools

            
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
        
        self.resiFitsDir="%s/resiFits"%(dataDest)
        self.resiCatDir="%s/resiCat"%(dataDest)
        self.destDir="%s/subImg"%(dataDest)
        self.preViewDir="%s/preview"%(dataDest)
        self.origPreViewDir="%s/orig_preview"%(dataDest)
        self.wcsDir="%s/wcs"%(dataDest)
            
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
                
        if not os.path.exists(self.resiFitsDir):
            os.system("mkdir -p %s"%(self.resiFitsDir))
        if not os.path.exists(self.resiCatDir):
            os.system("mkdir -p %s"%(self.resiCatDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir -p %s"%(self.destDir))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir -p %s"%(self.preViewDir))
        if not os.path.exists(self.origPreViewDir):
            os.system("mkdir -p %s"%(self.origPreViewDir))

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
            print('read_ra_center:%.5f, read_dec_center:%.5f, real_ra_center:%.5f, real_dec_center:%.5f'%(cra, cdec, ra_center, dec_center))
        else:
            print('%s, get wcs error'%(imgName))
            ra_center, dec_center = 0, 0
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** get WCS %s use %d seconds"%(imgName, runTime))
        print("********** get WCS %s use %d seconds"%(imgName, runTime))
        
        return wcsfile, ra_center, dec_center
              
def run1():
    
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
    srcPath00='/data1/G004_041_190124'
    dateStr='190124'
    camName='G041'
    curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(srcPath00, dstDir, tools, camName, curSkyId)

    try:
        tfiles0 = os.listdir(srcPath00)
        tfiles0.sort()
        for tfile in tfiles0:
            if tfile.find('mon_objt')>0: #G041_mon_objt_190124T10274817.fit.fz
                tfiles.append(tfile[:33])
        
        print("total has %d images"%(len(tfiles)))
        
        ra0, dec0 = -1000, -1000
        for i, timgName in enumerate(tfiles):
            
            tpath = "%s/%s.fz"%(srcPath00, timgName)
            if os.path.exists(tpath):
                tStr = "start diff: %s"%(timgName)
                tdiff.log.info(tStr)
                starttime = datetime.now()
                
                print("process %s"%(timgName))
                wcsfile, ra_center, dec_center = tdiff.getWCS(srcPath00, timgName, ra0, dec0)
                ra0, dec0 = ra_center, dec_center
                #os.system("cp %s/%s %s/%s"%(self.tmpCat, wcsfile, self.wcsDir, wcsfile))
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                tdiff.log.info("totalTime %d seconds, %s"%(runTime, timgName))
            else:
                print("%s not exist"%(tpath))
                
            if i>5:
                break

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

def evaluatePos(srcDir, oiFile, tiFile, mchPair, isAbs=False):
              
    tdata1 = np.loadtxt("%s/%s"%(srcDir, oiFile))
    tdata2 = np.loadtxt("%s/%s"%(srcDir, tiFile))
    tIdx1 = np.loadtxt("%s/%s"%(srcDir, mchPair)).astype(np.int)
    
    tMin = np.min([tdata1.shape[0], tdata2.shape[0]])
    percentage = tIdx1.shape[0]*1.0/tMin
    
    print("getMatchPosHmg: osn16:%d tsn16:%d osn16_tsn16_cm5:%d, pect:%.3f"%(tdata1.shape[0], tdata2.shape[0],tIdx1.shape[0],percentage))
    
    tIdx1 = tIdx1 - 1
    pos1 = tdata1[tIdx1[:,0]][:,0:2]
    pos2 = tdata2[tIdx1[:,1]][:,0:2]
    
    if isAbs:
        posDiff = np.fabs(pos1 - pos2)
    else:
        posDiff = pos1 - pos2
    tmean = np.mean(posDiff, axis=0)
    tmax = np.max(posDiff, axis=0)
    tmin = np.min(posDiff, axis=0)
    trms = np.std(posDiff, axis=0)
    xshift = tmean[0]
    yshift = tmean[1]
    xrms = trms[0]
    yrms = trms[1]
    print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
    
def test():
    
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
    srcPath00='/data1/G004_041_190124'
    dateStr='190124'
    camName='G041'
    curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(srcPath00, dstDir, tools, camName, curSkyId)
    
    tpath1 = '/data2/G003_034_190211'
    tpath2 = '/data2/G003_034_190227'
    fname1= 'G034_mon_objt_190211T12192603.fit.fz'
    fname2='G034_mon_objt_190227T12304321.fit.fz'
    
    ra0, dec0 = -1000, -1000
    wcsfile1, ra_center1, dec_center1 = tdiff.getWCS(tpath1, fname1, ra0, dec0)
    wcs1 = WCS('%s/%s'%(tdiff.tmpDir, wcsfile1))
    wcsfile2, ra_center2, dec_center2 = tdiff.getWCS(tpath2, fname2, ra0, dec0)
    wcs2 = WCS('%s/%s'%(tdiff.tmpDir, wcsfile2))
    
    os.system("cp %s/%s %s/%s"%(tpath1, fname1, tdiff.tmpDir, fname1))
    os.system("%s %s/%s"%(tdiff.funpackProgram, tdiff.tmpDir, fname1))
    os.system("cp %s/%s %s/%s"%(tpath2, fname2, tdiff.tmpDir, fname2))
    os.system("%s %s/%s"%(tdiff.funpackProgram, tdiff.tmpDir, fname2))
            
    fpar='sex_diff.par'
    sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
    tcat1 = tools.runSextractor('G034_mon_objt_190211T12192603.fit', tdiff.tmpDir, tdiff.tmpDir, fpar, sexConf)
    tcat2 = tools.runSextractor('G034_mon_objt_190227T12304321.fit', tdiff.tmpDir, tdiff.tmpDir, fpar, sexConf)
    
    tdata2 = np.loadtxt("%s/%s"%(tdiff.tmpDir, tcat2))
    tXY = tdata2[:,0:2]
    print(tXY[:3])
    tRaDec = wcs2.all_pix2world(tXY, 1)
    print(tRaDec[:3])
    tXY2 = wcs1.all_world2pix(tRaDec, 1)
    print(tXY2[:3])
    tdata2[:,0:2] = tXY2
    saveName = "%s_trans.cat"%(fname2.split(".")[0])
    savePath = "%s/%s"%(tdiff.tmpDir, saveName)
    np.savetxt(savePath, tdata2, fmt='%.4f')
    
    mchFile, nmhFile, mchPair = tools.runCrossMatch(tdiff.tmpDir, tcat1, saveName, 1)
    evaluatePos(tdiff.tmpDir, tcat1, saveName, mchPair)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    #run1()
    test()
    