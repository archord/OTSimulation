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
    
    def __init__(self):
        
        self.conn = False
        self.conn2 = False
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam3)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
    
    def queryParms(self, parms, ccdId, startTime, endTime, history=False):
        
        tableName = 'image_status_parameter'
        if history:
            tableName = 'image_status_parameter_his'
        
        sql = "select %s " \
            "from %s isp " \
            "inner join camera cam on cam.camera_id=isp.dpm_id and cam.name='%s' " \
            "where time_obs_ut>='%s' and time_obs_ut<'%s' " \
            "order by time_obs_ut asc"%(parms, tableName, ccdId, startTime, endTime)
        
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
            
    def getFWHM(self):
        
        parms = 'time_obs_ut, fwhm'
        ccdId = '021'
        startTime = '2018-02-04 10:54:42'
        endTime = '2018-02-04 23:54:42'
        
        tdatas = self.queryParms(parms, ccdId, startTime, endTime, history=True)
        print(tdatas[:3])
        
        tdatas=np.array(tdatas)
        print(tdatas[:3])
        
        dates = tdatas[:,0]
        fwhms = tdatas[:,1]
        print(dates[:3])
        print(fwhms[:3])
        
        plt.figure(figsize = (12, 12))
        plt.plot(dates, fwhms)
        plt.show()
        
        tIdx = (fwhms>0.5)&(fwhms<2.5)
        dates1 = dates[tIdx]
        fwhms1 = fwhms[tIdx]
        plt.figure(figsize = (12, 12))
        plt.plot(dates1, fwhms1)
        plt.show()
        
        dates2 = dates[10:-100]
        fwhms2 = fwhms[10:-100]
        plt.figure(figsize = (12, 12))
        plt.plot(dates2, fwhms2)
        plt.show()

    def getAllParm(self):
        
        parms = '*'
        ccdId = '021'
        startTime = '2018-02-04 10:54:42'
        endTime = '2018-02-04 23:54:42'
        
        tdatas = self.queryParms(parms, ccdId, startTime, endTime, history=True)
        print(tdatas[0])
        
        tdatas=np.array(tdatas)
        print(tdatas[0])
        
        dates = tdatas[:,1]
        backgrounds = tdatas[:,3]
        print(dates[:3])
        print(backgrounds[:3])
        
        plt.figure(figsize = (12, 12))
        plt.plot(dates, backgrounds)
        plt.title("backgrounds")
        plt.show()


if __name__ == '__main__':
    
    query = ImageParmQuery()
    #query.getFWHM()
    query.getAllParm()
    
