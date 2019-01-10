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
        
    def getFileList(self, camName, ffId):
        
        if len(camName)==4:
            camId = (int(camName[2])-1)*5+int(camName[3])
        
            sql = "select ff_id, ff_number, sky_id, img_name, img_path "\
                "from fits_file2 "\
                "where sky_id>0 and cam_id=%d and ff_id>'%d'  " \
                "order by ff_id limit 10"%(camId, ffId)
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
        else:
            print("error: camera name must like G021")
            rows = []
            
        return rows
    
