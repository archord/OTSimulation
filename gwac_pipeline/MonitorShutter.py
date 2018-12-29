# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import time
import math
import logging

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class GWACAutoFollowup:
    
    webServerIP1 = '172.28.8.8:8080'
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
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
            
    def sendTriggerMsg(self, tmsg):

        try:
            #sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            #tmsg = "%s: %s"%(sendTime, tmsg)
            msgURL = "http://%s/gwebend/sendTrigger2WChart.action?chatId=gwac006&triggerMsg="%(self.webServerIP1)
            turl = "%s%s"%(msgURL,tmsg)
            #self.log.debug(turl)
            
            msgSession = requests.Session()
            msgSession.get(turl, timeout=10, verify=False)
        except Exception as e:
            self.log.error(" send trigger msg error ")
            self.log.error(str(e))
            
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
    
        
    def queryShutterStatus(self, diffMinutes):
    
        '''
        1、图像质量不佳增加了细分状态：
          -11：快门常闭
          -12:快门半开
          -13:拉长
          -15:背景结构异常
          -16:杂散光大
        2、其它改变：
          -6:进入重做模板计数，但未做模板
          -7:中心计算失败
          '''
        sql = 'select cam.name, isp.astro_flag, isp.time_obs_ut, ff.img_name '\
            'from image_status_parameter isp '\
            'INNER JOIN fits_file2 ff on isp.ff_id=ff.ff_id '\
            'INNER JOIN camera cam on cam.camera_id=isp.dpm_id '\
            'where astro_flag>=-16 and astro_flag<=-11 and EXTRACT(EPOCH FROM timezone(\'utc\', now())-time_obs_ut)/60<%d'%(diffMinutes)
            
        return self.getDataFromDB(sql)

    def checkFlag(self, diffMinutes=2000):
        
        #diffMinutes = 2
        status = self.queryShutterStatus(diffMinutes)
        status=np.array(status)
        #print(status)
        
        statusN11 = status[status[:,1]==-11]
        statusN12 = status[status[:,1]==-12]
        statusN13 = status[status[:,1]==-13]
        statusN15 = status[status[:,1]==-15]
        statusN16 = status[status[:,1]==-16]
        
        cams = []
        for st in statusN11:
            tcam = st[0]
            if not tcam in cams:
                flag = st[1]
                timeUtc = st[2]
                fileName = st[3]
                tstr = 'Camera%s shutter close, flag=%d\n%s\n%s'%(tcam, flag,timeUtc,fileName)
                self.log.debug(tstr)
                self.sendTriggerMsg(tstr)
                cams.append(tcam)
                
        cams = []
        for st in statusN12:
            tcam = st[0]
            if not tcam in cams:
                flag = st[1]
                timeUtc = st[2]
                fileName = st[3]
                tstr = 'Camera%s shutter half open, flag=%d\n%s\n%s'%(tcam, flag,timeUtc,fileName)
                self.log.debug(tstr)
                self.sendTriggerMsg(tstr)
                cams.append(tcam)
                
        cams = []
        for st in statusN13:
            tcam = st[0]
            if not tcam in cams:
                flag = st[1]
                timeUtc = st[2]
                fileName = st[3]
                tstr = 'Camera%s star stretch, flag=%d\n%s\n%s'%(tcam, flag,timeUtc,fileName)
                self.log.debug(tstr)
                self.sendTriggerMsg(tstr)
                cams.append(tcam)

    def start(self):
                
        idx = 1
        checkMinutes = 2
        while True:
            
            try:
                self.checkFlag(checkMinutes)
                
            except Exception as e:
                self.log.error("%d run, sendObservationCommand error"%(idx))
                self.log.error(e)
            sleepTime = 2*60+3
            self.log.debug("\n\n*************%05d run, sleep %d seconds...\n"%(idx, sleepTime))
            if idx %30==1:
                self.sendTriggerMsg("shutter status check %d "%(idx))
            time.sleep(sleepTime)
            idx = idx + 1
            #if idx >1:
            #    break
                

if __name__ == '__main__':

    gwacAutoFollowUp = GWACAutoFollowup()
    gwacAutoFollowUp.start()
    

