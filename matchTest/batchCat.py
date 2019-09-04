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
        
        self.conn = psycopg2.connect(**self.connParam3)
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
        if not os.path.exists(self.catDir):
            os.system("mkdir -p %s"%(self.catDir))

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s, sky:%s, ffNum:%d\n %s"%(self.camName, self.skyName, self.ffNumber, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
        
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
    
    def getCat(self, srcDir, imgName):
        
        starttime = datetime.now()
        
        if os.path.exists(self.tmpDir):
            os.system("rm -rf %s/*"%(self.tmpDir))
        else:
            os.system("mkdir -p %s"%(self.tmpDir))
        
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

        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
        os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, self.objectImgCat, self.catDir, imgpre))
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        #self.log.info("********** get cat %s use %d seconds"%(imgName, runTime))
        print("********** get cat %s use %d seconds"%(imgName, runTime))

         
def run1():
    
    storePath = '/data/gwac_data/gwac_orig_fits'
    #toolPath = os.getcwd()
    toolPath = '/data/work/program/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "/data/gwac_diff_xy/data"
    logDest0 = "/data/gwac_diff_xy/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    tfiles = []
    #srcPath00='/data1/G004_041_190124'
    dateStr='190620'
    camName='G041'
    curSkyId='123'
    
    dstDir='%s/%s'%(dataDest0, dateStr)
    tdiff = BatchImageDiff(storePath, dstDir, tools, camName, curSkyId)
    
    skyId = 2577
    sql1 = "select date_str, cam_id from file_number where sky_id=%d ORDER BY date_str, cam_id"%(skyId)
    
    print(sql1)
    tquery = QueryData()
    tdates = tquery.query(sql1)
    
    print("total has %d date&ccd"%(len(tdates)))
    
    for i, tdate in enumerate(tdates):

        try:
            dateStr = tdate[0][2:8]
            camId = tdate[1]
            mountNum = int(camId/5) + 1
            ccdNum = camId%5
            if ccdNum==0:
                continue
            camName = '0%d%d'%(mountNum, ccdNum)
            tpath1 = '%s/%s/G00%d_%s'%(storePath, dateStr, mountNum,camName)
                
            sql1 = "select img_name " \
                "from fits_file2_his " \
                "where sky_id=%s and cam_id=%s and substr(img_path, 17, 6)='%s'  " \
                "order by img_name"%(skyId, camId, dateStr)
            
            print(sql1)
            tquery = QueryData()
            tfiles = tquery.query(sql1)
            
            print("total has %d images"%(len(tfiles)))
            
            for j, tname in enumerate(tfiles):
                
                tname00 = tname[0]
                tpath = "%s/%s"%(tpath1, tname00)
                tpathz = "%s/%s.fz"%(tpath1, tname00)
                if os.path.exists(tpath):
                    timgName = tname00
                elif os.path.exists(tpathz):
                    timgName = tname00 + '.fz'
                else:
                    print("%s not exist"%(tpath))
                    continue
                
                if j%25==0:
                    print("process %d %s"%(j, timgName))
                    tdiff.getCat(tpath1, timgName)
                
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)

def getSubCat():
    
    srcDir = "/data/gwac_diff_xy/data/190620/cat"
    dstDir = "/data/gwac_diff_xy/data/190620/cat"
    
    cats = os.listdir(srcDir)
    
    fnames = []
    datas = []
    for tcat in cats:
        spath1 = "%s/%s"%(srcDir,tcat)
        tdata = np.loadtxt(spath1)
        
        fnames.append(tcat)
        datas.append(tdata)
    
    np.savez_compressed('posTest.npz',fns=fnames, ds=datas)
        
            
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    #run1()
    getSubCat()