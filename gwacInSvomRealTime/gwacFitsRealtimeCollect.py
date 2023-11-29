# -*- coding: utf-8 -*-
import psycopg2

class GWACQuery:
    
    webServerIP1 = '172.28.8.28:8080'
    webServerIP2 = '10.0.10.236:9995'
    
    connParam={
        "host": "190.168.1.27",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    # 2 xinglong server
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
    # 4 beijing sever
    connParam4={
        "host": "10.0.10.236",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    
    fwhmQuery = "SELECT " \
        "from " \
        "update" 
    
    focusCommend = "insert "
    guideCommend = "insert "
    
    dirHRDImage = "/home/gwac/software/"
    #dirHRDImage = "/Volumes/Data/Documents/GitHub/Follow-up-trigger"
    
    def __init__(self):
        
        self.conn = False
        self.verbose = False
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam2)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.commit()
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
            print("error: getDataFromDB query data error")
            # self.log.error(" query data error ")
            # self.log.error(err)
            
        return rows

    '''
    startTimeUtc: 2021-10-31 12:35:33
    endTimeUtc: 2021-10-31 12:35:33
    '''
    def queryFitsListByTime(self, startTimeUtc, endTimeUtc):
        
        tsql = "SELECT cam.name camName, ff2.ff_id, ff2.img_name, ff2.img_path \
            from fits_file2 ff2 \
            INNER JOIN camera cam on ff2.cam_id=cam.camera_id \
            WHERE ff2.gen_time>='%s' and ff2.gen_time<='%s' \
            order by camName, ff_id"%(startTimeUtc, endTimeUtc)
        #self.log.debug(tsql)
        
        tresult = self.getDataFromDB(tsql)
        return tresult
          
    def test(self):
        try:
            startTimeUtc = '2023-11-29 10:46:32'
            endTimeUtc = '2023-11-29 10:47:32'
            tresult = self.queryFitsListByTime(startTimeUtc, endTimeUtc)
            print(tresult)
        except Exception as err:
            print(err)
            
if __name__ == '__main__':
    
    gwacQuery = GWACQuery()
    gwacQuery.test()
    

