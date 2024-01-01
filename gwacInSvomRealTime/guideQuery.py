# -*- coding: utf-8 -*-
import psycopg2
import datetime

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
        
        self.conn = psycopg2.connect(**self.connParam4)
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
    query the latest image_status_parameter of each camera
    query the max isp_id in image_status_parameter by each camera(dpm_id)
    '''
    def queryISPByCamera(self):
        
        tsql = "select cam.name as camName,time_obs_ut, mount_ra, mount_dec, img_center_ra, img_center_dec,obj_num, bg_bright, fwhm, s2n, avg_limit, avg_ellipticity "\
            "from image_status_parameter_his isp "\
            "INNER JOIN camera cam on cam.camera_id=isp.dpm_id "\
            "where isp_id in (select isp_id from( select dpm_id, max(isp_id) isp_id from image_status_parameter_his where dpm_id%5=0 GROUP BY dpm_id )aa)"
        # print(tsql)
        
        tresult = self.getDataFromDB(tsql)
        guideParms = []
        for td in tresult:
            camName=td[0]
            time_obs_ut=td[1]
            mount_ra=td[2]
            mount_dec=td[3]
            img_center_ra=td[4]
            img_center_dec=td[5]
            obj_num=td[6]
            bg_bright=td[7]
            fwhm=td[8]
            s2n=td[9]
            avg_limit=td[10]
            avg_ellipticity=td[11]
            guideParms.append({
                "camName":camName,
                "time_obs_ut":time_obs_ut,
                "mount_ra":mount_ra,
                "mount_dec":mount_dec,
                "img_center_ra":img_center_ra,
                "img_center_dec":img_center_dec,
                "obj_num":obj_num,
                "bg_bright":bg_bright,
                "fwhm":fwhm,
                "s2n":s2n,
                "avg_limit":avg_limit,
                "avg_ellipticity":avg_ellipticity
            })

        return guideParms
          
def chackGuideStatus():
    try:
        gwacQuery = GWACQuery()
        guideStatuss = gwacQuery.queryISPByCamera()
        print(guideStatuss)
        for td in guideStatuss:
            camName = td['camName']
            obsTime = td['time_obs_ut']
            mountRa = td['mount_ra']
            mountDec = td['mount_dec']
            imgCenterRa = td['img_center_ra']
            imgCenterDec = td['img_center_dec']

            currentTimeUtc = datetime.datetime.utcnow()
            timediff = (currentTimeUtc-obsTime).total_seconds()
            radiff = imgCenterRa-mountRa
            decdiff = imgCenterDec-mountDec
            print(camName, currentTimeUtc, obsTime, timediff, radiff, decdiff)
    except Exception as err:
        print(err)
            
if __name__ == '__main__':
    
    chackGuideStatus()

