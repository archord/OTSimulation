# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
from datetime import datetime
from datetime import timedelta
import time
import os

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
            
    
#name, img_name,gen_time,time_sub_second, ff_number, mag_aper, magerr_aper, flux, ra_d, dec_d,x, y, threshold
if __name__ == '__main__':
    
    tquery = QueryData()
    tdata = tquery.getData()
    
    print(len(tdata))
    
    regFile = "data/reg.txt"
    regData=[]
    for td in tdata:
        imgName=td[1]
        dateStr = td[2].strftime("%Y-%m-%d")
        timeStr = td[2].strftime("%H:%M:%S")
        regData.append([td[0],imgName,imgName,dateStr,timeStr,td[3]])
        recData = np.array([[td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12]]])
        objData = np.array([[2,imgName, td[4]]])
        #print(regData)
        recFile = 'data/%s_rec.txt'%(imgName.split('.')[0])
        objFile = 'data/%s_obj.txt'%(imgName.split('.')[0])
        if not os.path.exists(recFile):
            np.savetxt(recFile, recData, fmt='%s', delimiter=',')
        if not os.path.exists(objFile):
            np.savetxt(objFile, objData, fmt='%s', delimiter=',')
        
        #break
    regData=np.array(regData)
    np.savetxt(regFile, regData, fmt='%s', delimiter=',')
    