# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt


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
    
    QSciObj = "SELECT so_id, name, point_ra, point_dec, mag, status, trigger_status, found_usno_r2, found_usno_r2 " \
        "from science_object where auto_observation=true and status>=2"
    QFupObj = "SELECT fuo_id, fuo_name, fuo_type_id" \
        "from follow_up_object where ot_id="
    QFupRec = "SELECT * from follow_up_record where fuo_id=" \
        "inner join follow_up_observation fupObs on fupObs.fo_id=fupObj.fo_id and fupObs.filter='R' " 
    QOT2 = "SELECT * from ot_level2 where name="
    
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
            
    def autoFollowUp(self):
        
        sciObjs = self.getDataFromDB(self.QSciObj)
        for sciObj in sciObjs:
            tsql = "%s'%s'"%(self.QOT2,sciObj[1])
            ot2 = self.getDataFromDB(tsql)
            
            tsql = "%s%d"%(self.QFupObj,ot2[4])
            fupObjs = self.getDataFromDB(tsql)
            for fupObj in fupObjs:
                tsql = "%s%d"%(self.QFupRec,sciObj[0])
                fupRecords = self.getDataFromDB(tsql)

if __name__ == '__main__':
    
    gfup = GWACAutoFollowup()
    gfup.autoFollowUp()
    
