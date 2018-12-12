# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt

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
    
    def queryFilesNum(self):
                
        sql = "select substring(img_name, 15, 6) date_str, sky_id, cam_id, count(*) total "\
            "from fits_file2_his "\
            "where substring(img_name, 6, 7)='mon_obj' and gen_time>'2018-12-09 09:00:00' and gen_time<'2018-12-10 09:00:00' "\
            "GROUP BY date_str, sky_id, cam_id "\
            "ORDER BY date_str desc, total desc, sky_id, cam_id "
        
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
    
    def getFileList(self, skyId, camId, dateStr):
        
        sql = "select img_name, cam.name "\
            "from fits_file2_his ff2 "\
            "INNER JOIN camera cam on cam.camera_id=ff2.cam_id "\
            "where sky_id=%d and cam_id=%d and substring(img_name, 15, 6)='%s'  " \
            "order by img_name"%(skyId, camId, dateStr)
        
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

if __name__ == '__main__':
    
    query = QueryData()
    filesNum = query.queryFilesNum()
    
    for tnum in filesNum:
        
        if tnum[3]>1000 and tnum[2]%5>0:
            files = query.getFileList(tnum[1], tnum[2], tnum[0])
            print("%d,%d"%(tnum[3], len(files)))
            print(files[0])
            #break
    
