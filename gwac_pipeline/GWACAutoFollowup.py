# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import time
import math
import logging
from FollowUp import FollowUp

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class GWACAutoFollowup:
    
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
    connParam4={
        "host": "10.0.10.236",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    
    QSciObj = "SELECT so_id, name, point_ra, point_dec, mag, status, trigger_status, " \
        "found_usno_r2, found_usno_b2, discovery_time_utc, auto_loop_slow, type " \
        "from science_object where auto_observation=true and status>=1" 
    QFupObj = "SELECT fuo.fuo_id, fuo.fuo_name, fuoType.fuo_type_name " \
        "from follow_up_object fuo " \
        "inner join follow_up_object_type fuoType on fuo.fuo_type_id=fuoType.fuo_type_id " \
        "where fuo.ot_id=%d"
    QFupRec = "SELECT fupObs.auto_loop, fupRec.mag_cal_usno, fupRec.date_utc " \
        "from follow_up_record fupRec " \
        "inner join follow_up_observation fupObs on fupObs.fo_id=fupRec.fo_id "  \
        "where fupRec.filter='R' and fupRec.fuo_id=%d " \
        "order by fupRec.date_utc asc"
    QFupObs = "select limit_mag, expose_duration, auto_loop from follow_up_observation " \
        "where ot_id=%d and auto_loop=%d ORDER BY fo_id asc "
    QOT2 = "SELECT ot_id, mag from ot_level2_his where name='%s'"
    
    maxExpTime = 200
    maxMonitorTime = 100000 #minute 60
    
    stage2TriggerDelay = 2 #minute
    stage3TriggerDelay1 = 2 #minute
    stage3TriggerDelay2 = 5 #minute
    stageNTriggerDelay1 = 3 #minute
    stageNTriggerDelay2 = 3 #minute
    stageNTriggerDelay3 = 3 #minute
    
    stage1MagDiff = 1.2
    stage2MagDiff = 0.3
    stageNMagDiff1 = 0.3
    stageNMagDiff2 = 0.3
    
    
    def __init__(self):
        
        self.conn = False
        self.conn2 = False
        
        self.verbose = True
        
        self.log = logging.getLogger() #create logger
        self.log.setLevel(logging.DEBUG) #set level of logger
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s") #set format of logger
        logging.Formatter.converter = time.gmtime #convert time in logger to UCT
        filehandler = logging.FileHandler("otSim.log", 'w+')
        filehandler.setFormatter(formatter) #add format to log file
        self.log.addHandler(filehandler) #link log file to logger
        if self.verbose:
            streamhandler = logging.StreamHandler() #create print to screen logging
            streamhandler.setFormatter(formatter) #add format to screen logging
            self.log.addHandler(streamhandler) #link logger to screen logging
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam4)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def initSciObj(self, ot2Name):
    
        tsql = "update science_object set status=1, trigger_status=1, auto_observation=true where name='%s'"%(ot2Name)
        #self.log.debug(tsql)
        
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
            
        return rows

    def updateSciObjStatus(self, soId, status):
        
        tsql = "update science_object set status=%d where so_id=%d"%(status, soId)
        #self.log.debug(tsql)
        
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
            
    def updateSciObjTriggerStatus(self, soId, triggerStatus):
        
        tsql = "update science_object set trigger_status=%d where so_id=%d"%(triggerStatus, soId)
        #self.log.debug(tsql)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object trigger_status error ")
            self.log.error(err)
            
    def updateSciObjAutoLoopSlow(self, soId, autoLoop):
        
        tsql = "update science_object set auto_loop_slow=%d where so_id=%d"%(autoLoop, soId)
        #self.log.debug(tsql)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object trigger_status error ")
            self.log.error(err)
            
    def closeSciObjAutoObservation(self, soId):
        
        tsql = "update science_object set auto_observation=false where so_id=%d"%(soId)
        #self.log.debug(tsql)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            self.log.error(" update science_object auto_observation error ")
            self.log.error(err)
    
    def sendTriggerMsg(self, tmsg):

        try:
            #sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            #tmsg = "%s: %s"%(sendTime, tmsg)
            msgURL = "http://%s/gwebend/sendTrigger2WChart.action?chatId=gwac005&triggerMsg="%(self.webServerIP2)
            turl = "%s%s"%(msgURL,tmsg)
            #self.log.debug(turl)
            
            msgSession = requests.Session()
            msgSession.get(turl, timeout=10, verify=False)
        except Exception as e:
            self.log.error(" send trigger msg error ")
            self.log.error(str(e))
    
    #tobs=[{'filter':['R','B'],'expTime':40,'frameCount':1},{'filter':['R'],'expTime':40,'frameCount':2}]
    def sendObservationCommand(self, sciObj, observes=[],autoLoop=1,lastExpTime=-1, magdiff=0):

        try:
            self.log.debug(observes)
            
            otName = sciObj[1]
            ra = sciObj[2]
            dec = sciObj[3]
            for tobs in observes:
                #print(tobs)
                tfilters = tobs['filter']
                if lastExpTime>0:
                    if lastExpTime<self.maxExpTime:
                        expTime = int(lastExpTime * math.exp(0.4*magdiff))
                        if expTime>self.maxExpTime:
                            expTime = self.maxExpTime
                    else: # if expTime exceed maxExpTime, return false and stop observation
                        return True
                else:
                    expTime = tobs['expTime']
                frameCount = tobs['frameCount']
                for tf in tfilters:
                    tfilter = tf
                    fup = FollowUp(ra,dec,expTime,tfilter,frameCount,otName)
                    self.log.debug(fup.getFollowUpString())
                    fup.uploadFollowUpCommond(autoLoop)
        except Exception as e:
            self.log.error("sendObservationCommand error")
            self.log.error(e)
            
        return False
    
    #debug, info, warn, error
    def autoFollowUp(self):
        
        #so_id, name, point_ra, point_dec, mag, status, trigger_status, 
        #found_usno_r2, found_usno_b2, discovery_time_utc, auto_loop_slow, type
        sciObjs = self.getDataFromDB(self.QSciObj)
        self.log.debug("found %d sciObjs"%(len(sciObjs)))
        print(np.array(sciObjs))
        return
        for sciObj in sciObjs:

            status = sciObj[5] #status=1
            triggerStatus = sciObj[6] #trigger_status=1
            
            ot2Name = sciObj[1]
            tsql = self.QOT2%(ot2Name)
            ot2s = self.getDataFromDB(tsql)
            if len(ot2s)==0:
                self.log.debug("cannot find ot2 %s"%(ot2Name))
                return
            ot2=ot2s[0]
            
            self.log.debug("ot2: %s, status: %d, triggerStatus: %d"%(ot2Name, status, triggerStatus))
                
            if status == 1:
                
                foundTime = sciObj[9]
                curDateTime = datetime.now()
                curDateTime.replace(hour=curDateTime.hour-8)
                diffMinutes = (curDateTime - foundTime).total_seconds()/60.0
                
                if diffMinutes < self.maxMonitorTime:
                    if triggerStatus == 1:
                        tmsg = "Auto Trigger 60CM Telescope:\n" \
                           "%s %s Stage1.\n" \
                           "gwacMag:%.2f\nfirstObsMag:%.2f\n" \
                           "usnoRMag:%.2f\nusnoBMag:%.2f"%(sciObj[1],sciObj[11],ot2[1], sciObj[4],sciObj[7],sciObj[8])
                        self.log.debug(tmsg)
                        self.sendTriggerMsg(tmsg)
                        self.updateSciObjTriggerStatus(sciObj[0], 2)
                        
                    if diffMinutes>self.stage2TriggerDelay:
                        tobs=[{'filter':['B','R'],'expTime':30,'frameCount':1}]
                        isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, autoLoop=2)
                        if isExceedMaxTime:
                            self.closeSciObjAutoObservation(sciObj[0])
                            self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                        self.updateSciObjStatus(sciObj[0], 2)
                else: # exceed max monitor time, do not monitor this sciobj anymore
                    self.closeSciObjAutoObservation(sciObj[0])
                    self.log.warning("%s, %.2f exceed max monitor time(%dminutes), close monitor."%(ot2Name, diffMinutes, self.maxMonitorTime))
                    
            elif status > 1:
                                
                ot2Id = ot2[0]
                        
                tsql = self.QFupObs%(ot2Id, status)
                #limit_mag
                fupObserves = self.getDataFromDB(tsql)
                if len(fupObserves)==0:
                    self.log.debug("cannot find fupObserves %s"%(ot2Name))
                    return
                lastLimitMag = fupObserves[0][0]
                lastExpTime = fupObserves[0][1]
                
                tsql = self.QFupObj%(ot2Id)
                #fuo_id, fuo_name, fuo_type_name
                fupObjs = self.getDataFromDB(tsql)
                #print(fupObjs)
                
                for fupObj in fupObjs:
                    
                    #print(fupObj)
                    fuoId = fupObj[0]
                    tsql = self.QFupRec%(fuoId)
                    #auto_loop, mag_cal_usno, date_utc
                    fupRecords = self.getDataFromDB(tsql)
                    
                    fupRecords = np.array(fupRecords)
                    #print(fupRecords.shape)
                    #print(fupRecords[:5])
                    #break
                    
                    fupRecordN = fupRecords[fupRecords[:,0]==status]
                    fupRecordN1 = fupRecords[fupRecords[:,0]==(status-1)]
                    #print(fupRecordN)
                    #print(fupRecordN1)
                                        
                    #if find object in Nth folllow
                    if fupRecordN.shape[0]>0 and fupRecordN1.shape[0]>0:
                        fupRecordN = fupRecordN[0]
                        fupRecordN1 = fupRecordN1[0]
                        
                        magDiff = math.fabs(fupRecordN[1]-fupRecordN1[1])
                        
                        observeTime = fupRecordN[2]
                        curDateTime = datetime.now()
                        curDateTime.replace(hour=curDateTime.hour-8)
                        diffMinutes = (curDateTime - observeTime).total_seconds()/60.0
                        
                        if diffMinutes < self.maxMonitorTime:         
                            if status == 2:
                                if magDiff>=self.stage2MagDiff:
                                    if triggerStatus == status:
                                        tmsg = "Auto Trigger 60CM Telescope:\n" \
                                           "%s %s Stage%d.\n" \
                                           "gwacMag:%.2f\nfirstObsMag:%.2f\nlastObsMag:%.2f\n" \
                                           "usnoRMag:%.2f\nusnoBMag:%.2f"%(sciObj[1],sciObj[11],status, ot2[1], sciObj[4], fupRecordN[1], sciObj[7], sciObj[8])
                                        self.sendTriggerMsg(tmsg)
                                        self.updateSciObjTriggerStatus(sciObj[0], status+1)
                                    if diffMinutes>self.stage3TriggerDelay1:
                                        tobs=[{'filter':['B'],'expTime':40,'frameCount':1},
                                               {'filter':['R'],'expTime':40,'frameCount':2}]
                                        isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, status+1, lastExpTime, magDiff)
                                        if isExceedMaxTime:
                                            self.closeSciObjAutoObservation(sciObj[0])
                                            self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                                            break
                                        self.updateSciObjStatus(sciObj[0], status+1)
                                    break
                                else:
                                    self.sendTriggerMsg("%s %s Stage%d, magDiff: %.2f"%(sciObj[1],sciObj[11],status, magDiff))
                                    if diffMinutes>self.stage3TriggerDelay2:
                                        tobs=[{'filter':['B','R'],'expTime':30,'frameCount':1}]
                                        isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, status+1, lastExpTime, magDiff)
                                        if isExceedMaxTime:
                                            self.closeSciObjAutoObservation(sciObj[0])
                                            self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                                            break
                                        self.updateSciObjStatus(sciObj[0], status+1)
                                        self.updateSciObjAutoLoopSlow(sciObj[0], status-1)
                                        self.updateSciObjTriggerStatus(sciObj[0], status+1)
                                    break
                            elif status > 2:
                                if magDiff>=self.stageNMagDiff1:
                                    if triggerStatus == status:
                                        tmsg = "Auto Trigger 60CM Telescope:\n" \
                                           "%s %s Stage%d.\n" \
                                           "gwacMag:%.2f\nfirstObsMag:%.2f\nlastObsMag:%.2f\n" \
                                           "usnoRMag:%.2f\nusnoBMag:%.2f"%(sciObj[1],sciObj[11],status, ot2[1], sciObj[4], fupRecordN[1], sciObj[7], sciObj[8])
                                        self.sendTriggerMsg(tmsg)
                                        self.updateSciObjTriggerStatus(sciObj[0], status+1)
                                    if diffMinutes>self.stageNTriggerDelay1:
                                        tobs=[{'filter':['B'],'expTime':40,'frameCount':1},
                                               {'filter':['R'],'expTime':40,'frameCount':1}]
                                        isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, status+1, lastExpTime, magDiff)
                                        if isExceedMaxTime:
                                            self.closeSciObjAutoObservation(sciObj[0])
                                            self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                                            break
                                        self.updateSciObjStatus(sciObj[0], status+1)
                                    break
                                else:
                                    autoLoopIdx = sciObj[10]
                                    #print(autoLoopIdx)
                                    #print(fupRecords)
                                    fupRecordNk = fupRecords[fupRecords[:,0]==autoLoopIdx]
                                    fupRecordNk = fupRecordNk[0]
                                    #print(fupRecordNk)
                                    magDiffK = math.fabs(fupRecordN[1]-fupRecordNk[1])
                                    if magDiffK>=self.stageNMagDiff2:
                                        if triggerStatus == status:
                                            tmsg = "Auto Trigger 60CM Telescope:\n" \
                                               "%s %s Stage%d.\n" \
                                               "gwacMag:%.2f\nfirstObsMag:%.2f\nlastObsMag:%.2f\n" \
                                               "usnoRMag:%.2f\nusnoBMag:%.2f"%(sciObj[1],sciObj[11],status, ot2[1], sciObj[4], fupRecordN[1], sciObj[7], sciObj[8])
                                            self.sendTriggerMsg(tmsg)
                                            self.updateSciObjTriggerStatus(sciObj[0], status+1)
                                        if diffMinutes>self.stageNTriggerDelay2:
                                            tobs=[{'filter':['B','R'],'expTime':30,'frameCount':1}]
                                            isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, status+1, lastExpTime, magDiff)
                                            if isExceedMaxTime:
                                                self.closeSciObjAutoObservation(sciObj[0])
                                                self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                                                break
                                            self.updateSciObjStatus(sciObj[0], status+1)
                                            self.updateSciObjAutoLoopSlow(sciObj[0], status)
                                        break
                                    else:
                                        self.sendTriggerMsg("%s %s Stage%d, magDiff: %.2f"%(sciObj[1],sciObj[11],status, magDiffK))
                                        if diffMinutes>self.stageNTriggerDelay3:
                                            tobs=[{'filter':['B','R'],'expTime':30,'frameCount':1}]
                                            isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, status+1, lastExpTime, magDiffK)
                                            if isExceedMaxTime:
                                                self.closeSciObjAutoObservation(sciObj[0])
                                                self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                                                break
                                            self.updateSciObjStatus(sciObj[0], status+1)
                                            self.updateSciObjTriggerStatus(sciObj[0], status+1)
                                        break
                        
                        else:# exceed max monitor time, do not monitor this sciobj anymore
                            self.closeSciObjAutoObservation(sciObj[0])
                            self.log.warning("%s, %.2f exceed max monitor time(%dminutes), close monitor."%(ot2Name, diffMinutes, self.maxMonitorTime))
                            break
                        
                    elif fupRecordN.shape[0]==0 and fupRecordN1.shape[0]>0:
                        
                        self.log.warning("cannot find fupRecord[n] mag, use limit mag")
                        
                        fupRecordN1 = fupRecordN1[0]
                        
                        print(fupObserves)
                        limitMag = fupObserves[0][0]
                        magDiff = math.fabs(limitMag-fupRecordN1[1])
                        self.sendTriggerMsg("%s %s Stage%d, magDiff: %.2f"%(sciObj[1],sciObj[11],status, magDiff))
                        
                        tobs=[{'filter':['B','R'],'expTime':30,'frameCount':1}]
                        isExceedMaxTime = self.sendObservationCommand(sciObj, tobs, status+1, lastExpTime, magDiff)
                        if isExceedMaxTime:
                            self.closeSciObjAutoObservation(sciObj[0])
                            self.sendTriggerMsg("%s expTime exceed %d seconds, stop observation."%(ot2Name, self.maxExpTime))
                            break

                        self.updateSciObjStatus(sciObj[0], status+1)
                        self.updateSciObjTriggerStatus(sciObj[0], status+1)
                        break
                    
                    else:
                        self.closeSciObjAutoObservation(sciObj[0])
                        self.log.warning("cannot find fupRecord[n-1] mag, stop obs")
                        self.sendTriggerMsg("%s Stage%d cannot find fupRecord[n-1], stop observation."%(ot2Name, status))
                        break

    def start(self):
        
        ot2Name = 'G181211_C03732'
        self.initSciObj(ot2Name)
        
        idx = 1
        while True:
            
            self.autoFollowUp()
            
            sleepTime = 2
            self.log.debug("\n\n*************%05d run, sleep %d seconds...\n"%(idx, sleepTime))
            #print("\n*************%05d run, sleep %d seconds...\n"%(idx, sleepTime))
            time.sleep(sleepTime)
            idx = idx + 1
            if idx >1:
                break
                

if __name__ == '__main__':

    gwacAutoFollowUp = GWACAutoFollowup()
    gwacAutoFollowUp.start()
    

