# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import math

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class AnalysisOT2:
    
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
        
        self.conn = psycopg2.connect(**self.connParam3)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
    
    def queryOT2Num(self):
                
        sql = "select num, count(*) " \
            "from( " \
            "SELECT dpm_id, first_ff_number, count(*) num " \
            "from ot_level2 " \
            "where found_time_utc>'2018-12-01 09:53:04' " \
            "GROUP BY dpm_id, first_ff_number " \
            ")as aa " \
            "GROUP BY num " \
            "ORDER BY num asc"
        
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
    
    query = AnalysisOT2()
    rows = query.queryOT2Num()
    
    tdata = np.array(rows)
    print(tdata.shape)
    print(tdata[:3])
    x = tdata[:,0]
    y = tdata[:,1]
    #y = np.log10(y)
    
    for i in range(y.shape[0]):
        if i>0:
            y[i]=y[i]+y[i-1]
            
    y = y/y[-1]
    
    x=x[10:]
    y=y[10:]
    
    plt.plot(x,y)
    plt.show()
    
