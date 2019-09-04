# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class QueryData:
    
    connParam={
        "host": "192.168.56.103",
        "port": "5432",
        "dbname": "objectanalyze",
        "user": "gwac",
        "password": "xyag902"
        }
    
    def __init__(self):
        
        self.conn = False
        self.conn2 = False
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def insertData(self,name,status,name1,name2,orbit):
        
        sql = "insert into object(obj_name,status,name1,name2,orbit_info) "\
            "values('%s','%s','%s','%s','%s');"%(name,status,name1,name2,orbit)
        print(sql)
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            cur.commit()
            self.closeDb()
        except Exception as err:
            print(" insert data error ")
            print(err)
            
    

if __name__ == '__main__':
    
    dataFile = 'e:/resource/obj_records3.txt'
    #tquery = QueryData()
    #tquery.connDb()
    
    tdatas = np.loadtxt(dataFile,delimiter=',')
    print(tdatas[:3])
    
    for tdata in tdatas:
        
        sql = "insert into radar_observation_record(oe_id,milliseconds, rcs) "\
            "values(2,%f,%f);"%(tdata[0]-45.5,tdata[1]/10)
        print(sql)
        #tquery.closeDb()
        #break
    