# -*- coding: utf-8 -*-
import numpy as np
import os
import psycopg2
import requests
import traceback
from datetime import datetime

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class QueryData:
    
    connParam={
        "host": "172.28.8.28",
        "port": "5432",
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
        
    def getData(self):
        
        tsql = "select cam.name, ff2.img_name,ff2.gen_time,ff2.time_sub_second, ff2.ff_number,  "\
            "oor.mag_aper, oor.magerr_aper, oor.flux, oor.ra_d, oor.dec_d,oor.x, oor.y, oor.threshold "\
            "from move_object movObj "\
            "INNER JOIN move_object_record movRec on movObj.mov_id=movRec.mov_id "\
            "INNER JOIN ot_observe_record_his oor on oor.oor_id=movRec.oor_id "\
            "INNER JOIN fits_file2_his ff2 on ff2.ff_id=oor.ff_id "\
            "INNER JOIN camera cam on cam.camera_id=ff2.cam_id "\
            "where movObj.mov_id=417540 "\
            "ORDER BY ff2.gen_time"
        print(tsql)
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            rows = cur.fetchall()
            cur.close()
            self.closeDb()
            return rows
        except Exception as err:
            print(" query data error ")
            print(err)
            
def regImg(tdata):
    
    camName=tdata[0]
    imgName=tdata[1]
    imgPath=tdata[2]
    dateStr=tdata[3]
    microSecond=tdata[4]
    
    try:
        #serverIP='172.28.8.8'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/regOrigImg.action"%(serverIP)
        
        values = {'camId': camName, 
                  'imgName': imgName, 
                  'imgPath': imgPath, 
                  'genTime': dateStr, 
                  'microSecond': microSecond}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def sendRecord(tpath, fname, fileType='crsot1'):
        
    try:
        serverIP='172.28.9.14'
        #serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/commonFileUpload.action"%(serverIP)
        
        values = {'fileType': fileType}
        
        files = []
        
        tpath = "%s/%s"%(tpath, fname)
        files.append(('fileUpload', (fname,  open(tpath,'rb'), 'text/plain')))
        
        msgSession = requests.Session()
        r = msgSession.post(turl, files=files, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)

def testUpload():
    
    tquery = QueryData()
    tdata = tquery.getData()
    
    for td in tdata:
        imgName=td[1]
        dateStr = td[2].strftime("%Y-%m-%d %H:%M:%S")
        regData = [td[0],imgName,imgName,dateStr,td[3]]
        #regImg(regData)
        
        
        recDataStr = "%d,%f,%f,%f,%f,%f,%f,%f,%f"%(td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12])
        print(recDataStr)
        
        rootPath='data2'
        tfile = '%s.record'%(imgName.split('.')[0])
        tpath = "%s/%s"%(rootPath, tfile)
        if not os.path.exists(tpath):
            ff=open(tpath, 'w')
            ff.write(recDataStr)
            ff.close()
        sendRecord('data2', tfile, fileType='crsot1')
        '''
        '''
        objDataStr = "%d,%s,%d"%(2,imgName, td[4])
        print(objDataStr)
        
        rootPath='data3'
        tfile = '%s.obj'%(imgName.split('.')[0])
        tpath = "%s/%s"%(rootPath, tfile)
        if not os.path.exists(tpath):
            ff=open(tpath, 'w')
            ff.write(objDataStr)
            ff.close()
        sendRecord('data3', tfile, fileType='objcorr')
        #break
        
if __name__ == "__main__":
    
    testUpload()