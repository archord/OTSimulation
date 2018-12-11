# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import time
import math

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class GWACAutoFollowup:
    
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
    
    QSciObj = "SELECT so_id, name, point_ra, point_dec, mag, status, trigger_status, " \
        "found_usno_r2, found_usno_b2, discovery_time_utc, auto_loop_slow, type " \
        "from science_object where status>=1"  #auto_observation=true and 
    QFupObj = "SELECT fuo.fuo_id, fuo.fuo_name, fuoType.fuo_type_name" \
        "from follow_up_object fuo" \
        "inner join follow_up_object_type fuoType on fuo.fuo_type_id=fuoType.fuo_type_id " \
        "where fuo.ot_id=%d"
    QFupRec = "SELECT fupObs.auto_loop, fupRec.mag_cal_usno, fupRec.date_utc " \
        "from follow_up_record fupRec" \
        "inner join follow_up_observation fupObs on fupObs.fo_id=fupRec.fo_id and fupObs.filter='R' "  \
        "where fupRec.fuo_id=%d " \
        "order by fupRec.date_utc desc"
    QOT2 = "SELECT ot_id, mag from ot_level2 where name='%s'"
    
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
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam3)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
    
    def getDataFromDB(self, sql):
                
        tsql = sql
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            rows = cur.fetchall()
            cur.close()
            self.closeDb()
        except Exception as err:
            rows = []
            print(" query science_object error ")
            print(err)
            
        return rows

    def updateSciObjStatus(self, soId, status):
        
        tsql = "update science_object set status=%d where so_id=%d"%(status, soId)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            print(" update science_object status error ")
            print(err)
            
    def updateSciObjTriggerStatus(self, soId, triggerStatus):
        
        tsql = "update science_object set trigger_status=%d where so_id=%d"%(triggerStatus, soId)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            print(" update science_object trigger_status error ")
            print(err)
            
    def updateSciObjAutoLoopSlow(self, soId, autoLoop):
        
        tsql = "update science_object set auto_loop_slow=%d where so_id=%d"%(autoLoop, soId)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            self.conn.commit()
            cur.close()
            self.closeDb()
        except Exception as err:
            print(" update science_object trigger_status error ")
            print(err)
    
    def sendTriggerMsg(tmsg):

        try:
            #sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            #tmsg = "%s: %s"%(sendTime, tmsg)
            msgURL = "http://172.28.8.8:8080/gwebend/sendTrigger2WChart.action?chatId=gwac004&triggerMsg="
            turl = "%s%s"%(msgURL,tmsg)
            
            msgSession = requests.Session()
            msgSession.get(turl, timeout=10, verify=False)
        except Exception as e:
            print(str(e))
            
    def sendObservationCommand():

        try:
            print("trigger 60")
        except Exception as e:
            print(str(e))
            
    def autoFollowUp(self):
        
        #so_id, name, point_ra, point_dec, mag, status, trigger_status, 
        #found_usno_r2, found_usno_b2, discovery_time_utc, auto_loop_slow, type
        sciObjs = self.getDataFromDB(self.QSciObj)
        for sciObj in sciObjs:

            status = sciObj[5] #status=1
            triggerStatus = sciObj[6] #trigger_status=1
            
            ot2Name = sciObj[1]
            tsql = self.QOT2%(ot2Name)
            ot2s = self.getDataFromDB(tsql)
            ot2=ot2s[0]
                
            if status == 1:
                if triggerStatus == 1:
                    tmsg = "Auto Trigger 60CM Telescope:\n" \
                       "%s %s Stage1.\n" \
                       "gwacMag:%.2f\nfirstObsMag:%.2f\n" \
                       "usnoRMag:%.2f\nusnoBMag:%.2f"%(sciObj[1],sciObj[11],ot2[1], sciObj[4],sciObj[7],sciObj[8])
                    self.sendTriggerMsg(tmsg)
                    self.updateSciObjTriggerStatus(sciObj[0], 2)
                foundTime = sciObj[9]
                curDateTime = datetime.now()
                curDateTime.replace(hour=curDateTime.hour-8)
                diffMinutes = (curDateTime - foundTime).total_seconds()/60.0
                if diffMinutes>self.stage2TriggerDelay:
                    self.sendObservationCommand()
                    self.updateSciObjStatus(sciObj[0], 2)
                    
            elif status > 1:
                                
                ot2Id = ot2[0]
                tsql = self.QFupObj%(ot2Id)
                
                #fuo_id, fuo_name, fuo_type_name
                fupObjs = self.getDataFromDB(tsql)
                for fupObj in fupObjs:
                    fuoId = fupObj[0]
                    tsql = self.QFupRec%(fuoId)
                    #auto_loop, mag_cal_usno, date_utc
                    fupRecords = self.getDataFromDB(tsql)
                    
                    fupRecordN = fupRecords[fupRecords[:,0]==status]
                    fupRecordN1 = fupRecords[fupRecords[:,0]==(status-1)]
                    magDiff = math.fabs(fupRecordN[1]-fupRecordN1[1])
                
                    foundTime = fupRecordN[2]
                    curDateTime = datetime.now()
                    curDateTime.replace(hour=curDateTime.hour-8)
                    diffMinutes = (curDateTime - foundTime).total_seconds()/60.0
                    
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
                                self.sendObservationCommand()
                                self.updateSciObjStatus(sciObj[0], status+1)
                        else:
                            if diffMinutes>self.stage3TriggerDelay2:
                                self.sendObservationCommand()
                                self.updateSciObjStatus(sciObj[0], status+1)
                                self.updateSciObjAutoLoopSlow(sciObj[0], status-1)
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
                                self.sendObservationCommand()
                                self.updateSciObjStatus(sciObj[0], status+1)
                        else:
                            autoLoopIdx = sciObj[10]
                            fupRecordNk = fupRecords[fupRecords[:,0]==autoLoopIdx]
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
                                    self.sendObservationCommand()
                                    self.updateSciObjStatus(sciObj[0], status+1)
                                    self.updateSciObjAutoLoopSlow(sciObj[0], status)
                            else:
                                if diffMinutes>self.stageNTriggerDelay3:
                                    self.sendObservationCommand()
                                    self.updateSciObjStatus(sciObj[0], status+1)
                        
                        

if __name__ == '__main__':

    idx = 1
    #gwacAutoFollowUp = GWACAutoFollowup()
    #gwacAutoFollowUp.autoFollowUp()
    
    ''' '''
    while True:
        try:
            gwacAutoFollowUp = GWACAutoFollowup()
            gwacAutoFollowUp.autoFollowUp()
            time.sleep(10)
            idx = idx + 1
        except Exception as e:
            print(str(e))
    

