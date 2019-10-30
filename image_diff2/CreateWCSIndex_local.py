# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import time
import logging
import os
from astropy.wcs import WCS
from datetime import datetime
import traceback
import paramiko
from astrotools import AstroTools
import sys

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class GWACWCSIndex:
    
    orgImgRoot = '/data/gwac_data/gwac_orig_fits'
    wcsIdxRoot = '/data/gwac_data/gwac_wcs_idx'
    webServerIP1 = '172.28.8.28:8080'
    webServerIP2 = '10.0.10.236:9995'
    
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
    
    
    webUser  =  'gwac'
    webPassword  =  'xyag902'
    webIp = '172.28.8.8'
    
    
    def __init__(self):
        
        self.conn = False
        
        self.imgSize = (4136, 4096)
        self.templateImg = 'ti.fit'
        self.tmpRoot="/dev/shm/gwacWCS"
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        if not os.path.exists(self.templateDir):
            os.system("mkdir -p %s"%(self.templateDir))
        
        #/home/gwac/img_diff_xy/image_diff
        #/data/work/program/image_diff
        self.toolPath = '/home/gwac/img_diff_xy/image_diff'
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        
        #logPath = os.getcwd()
        self.tools = AstroTools(self.toolPath, "gwac_wcs")
        self.log = self.tools.log
    
    def makeTemplate(self, tparm):
        
        try:
            starttime = datetime.now()
            #print(tparm)
            tRaDec = np.array([])
            os.system("rm -rf %s/*"%(self.templateDir))
            
            imgName=tparm['img_name'].decode("utf-8") 
            fwhm=tparm['fwhm']
            ffNumber=tparm['ff_number']
            objNum=tparm['obj_num']
            imgPath=tparm['img_path'].decode("utf-8") 
            
            tmsgStr = "select %s as template, min fwhm %.2f"%(imgName, fwhm)
            print(tmsgStr)
            self.log.info(tmsgStr)
            self.tools.sendTriggerMsg(tmsgStr)
            
            os.system("rm -rf %s/*"%(self.templateDir))
    
            #oImgf = "%s/%s"%(imgPath,imgName)
            oImgf = imgPath
            print(oImgf)
            oImgfz = "%s.fz"%(imgPath)
            if os.path.exists(oImgfz):
                os.system("cp %s %s/%s.fz"%(oImgfz, self.templateDir, self.templateImg))
                os.system("%s %s/%s.fz"%(self.funpackProgram, self.templateDir, self.templateImg))
            elif os.path.exists(oImgf):
                os.system("cp %s %s/%s"%(oImgf, self.templateDir, self.templateImg))
            else:
                self.log.warning("%s not exist"%(oImgf))
                return
                
            fieldId, ra,dec = self.tools.removeHeaderAndOverScan(self.templateDir, self.templateImg)
            sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
            fpar='sex_diff.par'
            tmplCat, isSuccess = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf, cmdStatus=0)
            
            sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
            tmplCat, isSuccess = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf, cmdStatus=0, outSuffix='_ldac.fit')
            
            self.tools.ldac2fits('%s/%s'%(self.templateDir,tmplCat), '%s/ti_cat.fit'%(self.templateDir))
            
            tpath = "%s/%s"%(self.templateDir,tmplCat)
            runSuccess = self.tools.runWCS(self.templateDir,'ti_cat.fit', ra, dec)
            #ccdName = self.origTmplImgName[:4]
            #runSuccess = self.tools.runWCSRemotePC780(self.templateDir,'ti_cat.fit', ra, dec, ccdName)
            
            if runSuccess:
                twcs = WCS('%s/ti_cat.wcs'%(self.templateDir))
                height = self.imgSize[0]
                width = self.imgSize[1]
                tXYs=[]
                tXYs.append((width/2,height/2))
                tXYs.append((0,0))
                tXYs.append((0,height-1))
                tXYs.append((width-1,height-1))
                tXYs.append((width-1,0))
                tXYs = np.array(tXYs)
                
                try:
                    tRaDec = twcs.all_pix2world(tXYs, 1)
                    self.log.info('read_ra_dec:(%.5f, %.5f), real_dec_center:(%.5f, %.5f)'%(ra, dec, tRaDec[0][0], tRaDec[0][1]))
                except Exception as e:
                    self.log.error(e)
                    runSuccess = False
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
                    self.log.error('make template %s, xy to radec error'%(imgName))
                
                objName = 'ti.fit'
                bkgName = 'ti_bkg.fit'
                badPixCat = self.tools.processBadPix(objName, bkgName, self.templateDir, self.templateDir)
                
                imgPre = imgName.split('.')[0]
                tpaths = imgPath.split('/')  #/data2/G004_041_191015/G041_Mon_objt_191015T20282227.fit
                tpath0 = tpaths[-2]
                tcamName = tpath0[:8]
                tdateStr = tpath0[9:]
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
                
                try:
                    ssh.connect(self.webIp, username=self.webUser, password=self.webPassword)
                    
                    #/data/gwac_data/gwac_wcs_idx/12854925/G003_031/180210
                    storePath = "%s/%s/%s/%s"%(self.wcsIdxRoot,fieldId,tcamName, tdateStr)
                    tcmd = "mkdir -p %s;"%(storePath)
                    ssh.exec_command(tcmd)
                    time.sleep(10)
                    
                    fitImg = "%s/%s"%(self.templateDir, self.templateImg)
                    cat = "%s/ti.cat"%(self.templateDir)
                    catFit = "%s/ti_cat.fit"%(self.templateDir)
                    wcs = '%s/ti_cat.wcs'%(self.templateDir)
                    badPix = '%s/%s'%(self.templateDir, badPixCat)
                    
                    if os.path.exists(fitImg) and os.path.exists(cat) and os.path.exists(catFit) \
                        and os.path.exists(wcs) and os.path.exists(badPix):
                        print("start copy to remote dir %s"%(storePath))
                        ftp = ssh.open_sftp()
                        ftp.put(fitImg,"%s/%s.fit"%(storePath, imgPre))
                        ftp.put(cat,"%s/%s.cat"%(storePath, imgPre))
                        ftp.put(catFit,"%s/%s_cat.fit"%(storePath, imgPre))
                        ftp.put(wcs,"%s/%s.wcs"%(storePath, imgPre))
                        ftp.put(badPix,"%s/%s_badpix.cat"%(storePath, imgPre))
                        print("copy success")
                    elif not os.path.exists(fitImg):
                        runSuccess = False
                        print("%s is not exist"%(fitImg))
                    elif not os.path.exists(cat):
                        runSuccess = False
                        print("%s is not exist"%(cat))
                    elif not os.path.exists(catFit):
                        runSuccess = False
                        print("%s is not exist"%(catFit))
                    elif not os.path.exists(wcs):
                        runSuccess = False
                        print("%s is not exist"%(wcs))
                    elif not os.path.exists(badPix):
                        runSuccess = False
                        print("%s is not exist"%(badPix))
                    
                            
                except paramiko.AuthenticationException:
                    self.log.error("Authentication Failed!")
                    runSuccess = False
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
                except paramiko.SSHException:
                    self.log.error("Issues with SSH service!")
                    runSuccess = False
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
                except Exception as e:
                    self.log.error('make template %s, copy data to dest error'%(imgName))
                    self.log.error(str(e))
                    runSuccess = False
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
            
            else:
                self.log.error('make template %s, get wcs error'%(imgName))
            
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            self.log.info("********** make template %s use %d seconds"%(imgName, runTime))
            
        except Exception as e:
            runSuccess = False
            self.log.error(e)
            tstr = traceback.format_exc()
            self.log.error(tstr)
            tmsgStr = "%s make template error"%(imgName)
            self.tools.sendTriggerMsg(tmsgStr)
        
        return runSuccess, tRaDec
    
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam2)
        
    def closeDb(self):
        self.conn.close()
        
    def getDataFromDB(self, sql):
                
        tsql = sql
        #self.log.debug(tsql)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            rows = cur.fetchall()
            cur.close()
            self.closeDb()
        except Exception as err:
            rows = []
            self.log.error(" query data error ")
            self.log.error(err)
            
        return np.array(rows)
    
    def queryObs(self, camName):
    
        tsql = "select ors_id, date_str, sky_id, cam_id, img_num "\
                "from observation_record_statistic ors "\
                "INNER JOIN camera cam on cam.camera_id=ors.cam_id "\
                "where do_wcs=false and cam.name='%s' "\
                "ORDER BY ors_id "%(camName)
        print(tsql)
        
        return self.getDataFromDB(tsql)
    
    def queryImgParm(self, obs, isHis='_his'):
    
        tsql = "SELECT ff.img_name, isp.fwhm, ff.ff_number, isp.obj_num, isp.time_obs_ut, ff.ff_id, ff.img_path "\
            "from image_status_parameter%s isp "\
            "INNER JOIN fits_file2%s ff on isp.ff_id=ff.ff_id "\
            "where isp.fwhm>1 and ff.sky_id=%s and ff.cam_id=%s and to_char(ff.gen_time, 'YYMMDD')='%s' "\
            "ORDER BY ff_number"%(isHis, isHis, obs[2], obs[3], obs[1])
        
        trst = self.getDataFromDB(tsql)
        
        return trst
        
    def updateHasWCS(self, orsId, imgNum, minTime, maxTime, hasWCS='true'):
        
        startTime = datetime.strftime(minTime, "%Y-%m-%d %H:%M:%S")
        endTime = datetime.strftime(maxTime, "%Y-%m-%d %H:%M:%S")
            
        tsql = "update observation_record_statistic set has_wcs=%s, real_img_num=%d, " \
            "start_obs_time='%s', end_obs_time='%s' where ors_id=%s"%(hasWCS, imgNum, startTime, endTime, orsId)
        #print(tsql)
        
        try:
            self.connDb()
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object status error ")
            self.log.error(err)
            
    def updateDoWCS(self, orsId, doWCS='true'):
            
        tsql = "update observation_record_statistic set do_wcs=%s where ors_id=%s"%(doWCS, orsId)
        #print(tsql)
        
        try:
            self.connDb()
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object status error ")
            self.log.error(err)
            
    def updateWCSCoors(self, orsId, tRaDecs):
        
        rd = tRaDecs
        
        tsql = "update observation_record_statistic set center_ra=%f, center_dec=%f, " \
            "left_top_ra=%f, left_top_dec=%f, left_bottom_ra=%f, left_bottom_dec=%f, "\
            "right_top_ra=%f, right_top_dec=%f, right_bottom_ra=%f, right_bottom_dec=%f where ors_id=%s" \
            %(rd[0][0], rd[0][1], rd[1][0], rd[1][1], rd[2][0], rd[2][1], rd[3][0], rd[3][1],rd[4][0], rd[4][1], orsId)
        #print(tsql)
        try:
            self.connDb()
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object status error ")
            self.log.error(err)
            
    def insertObsWcs(self, orsId, tparms, getWCS='true'):
        
        #print(orsId)
        #print(tparms)
        tsql = "insert into observation_record_statistic_wcs(ff_id,fwhm,star_num,ors_id,get_wcs)"\
            "values(%d,%f,%d,%s,%s)"%(tparms[5],tparms[1],tparms[3],orsId,getWCS)
        #print(tsql)
        
        try:
            self.connDb()
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object status error ")
            self.log.error(err)
    
    def checkImg(self, obs, imgParms):
        
        dateStr = obs[1]
        skyId = int(obs[2])
        camId = int(obs[3])
        mountId = int(camId/5)+1
        camId2 = camId%5
        if camId2==0:
            mountId = mountId - 1
            camId2 = 5
        camName = "G%03d_%02d%d"%(mountId, mountId, camId2)
        #print(dateStr,skyId, camName)
        #fullPath = "%s/%s/%s"%(self.orgImgRoot, dateStr, camName) #/data2/G002_023_191015 /data/gwac_data/gwac_orig_fits/191015/G004_043
        
        tparms = []
        for tparm in imgParms:
            imgPath = tparm[6]
            #imgPath = "%s/%s"%(fullPath, tparm[0])
            imgPathfz = "%s.fz"%(imgPath)
            #print(imgPathfz)
            if os.path.exists(imgPathfz) or os.path.exists(imgPath):
                tparms.append((tparm[0],tparm[1],tparm[2],tparm[3],tparm[6],tparm[5]))
        
        dtype = [('img_name', 'S40'), ('fwhm', float), ('ff_number', int), ('obj_num', int), ('img_path', 'S100'), ('ff_id', int)]
        trst=np.array(tparms, dtype=dtype)
        return trst
    
    def doAstrometry(self, orsId, tparms):
        
        doSuccess = False
        sortParms = np.sort(tparms,order='fwhm')
        #print(sortParms)
        for i in range(3):
            runSuccess, tRaDec = self.makeTemplate(sortParms[i])
            if runSuccess:
                doSuccess = True
                self.updateWCSCoors(orsId, tRaDec)
                self.insertObsWcs(orsId, sortParms[i])
                break
            else:
                print("%dth run failure, try next image"%(i+1))
                #break
        
        return doSuccess
        
    def createWCS(self, camName, minNum=50):
        
        tobs = self.queryObs(camName)
        if tobs.shape[0]>0:
            for obs in tobs:
                print(obs)
                orsId = obs[0]
                dateStr = obs[1]
                self.updateDoWCS(orsId)
                camId = int(obs[3])
                if int(orsId)<80 or camId%5==0:
                    continue
                imgParms = self.queryImgParm(obs)
                if imgParms.shape[0]==0:
                    imgParms = self.queryImgParm(obs, " ")
                if imgParms.shape[0]>minNum:
                    timeObsUt = imgParms[:,4]
                    minTime = np.min(timeObsUt)
                    maxTime = np.max(timeObsUt)
                    #self.log.debug(imgParms.shape[0])
                    tparms = self.checkImg(obs, imgParms)
                    tnum = tparms.shape[0]
                    
                    tstr = "%s,%s,%s observe %s img, %d has parameter, %d still in local path."\
                        %(obs[1], obs[2], obs[3], obs[4], imgParms.shape[0], tnum)
                    self.log.debug(tstr)
                    print(tstr)
                    
                    if tnum<minNum:
                        print("%s,%s,%s has %d images, small than minimum %d number, skip"%(obs[1], obs[2], obs[3], tnum, minNum))
                        self.updateHasWCS(orsId, tnum, minTime, maxTime, 'false')
                    else:
                        if tnum>100:
                            tparms = tparms[25:-25]
                            doSuccess = self.doAstrometry(orsId, tparms)
                        else:
                            doSuccess = self.doAstrometry(orsId, tparms)
                        if doSuccess:
                            self.updateHasWCS(orsId, tnum, minTime, maxTime, 'true')
                        #break

#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python
if __name__ == '__main__':
    
    if len(sys.argv)>=2:
        camName = sys.argv[1]
        if len(camName)==4:
            camName = camName[1:]
            wcsIdx = GWACWCSIndex()
            wcsIdx.createWCS(camName)
        else:
            print("error: camera name must like G021")
    else:
        print("run: python Scheduling.py cameraName(G021)")
            