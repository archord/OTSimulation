# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import os
import psycopg2


class MeteorRecord:
    
    connParam={
        "host": "10.0.3.62",
        "port": "5433",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    
    def __init__(self):
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def getObjRecord(self, dateStr):
        
        sql = "select oorh1.date_ut, oorh1.ff_number, oorh1.x_temp, oorh1.y_temp, oorh1.ra_d, oorh1.dec_d, oorh1.mag_aper, oorh1.magerr_aper, oorh1.time_sub_second, cam.name, osky.sky_name "\
            "from ot_observe_record_his oorh1 "\
            "INNER JOIN camera cam on oorh1.dpm_id=cam.camera_id "\
            "INNER JOIN observation_sky osky on osky.sky_id=oorh1.sky_id "\
            "where oorh1.data_produce_method='1' and oorh1.date_str='%s' "\
            "ORDER BY oorh1.dpm_id, oorh1.sky_id, oorh1.date_ut, oorh1.ra_d"%(dateStr)

        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        f = open(r"all_move_object/%sall.txt"%(dateStr), "w")
        f.write("date_ut, frame_number, x_temp, y_temp, ra_d, dec_d, mag_aper,magerr_aper,seconds,camera,sky\n")
        for row in rows:
            f.write("%s, %d, %f, %f, %f, %f, %f, %f, %d, %s, %s\n"%row)
        f.close()
        cur.close()
        
    '''
    *startDate-endDate: 从数据库查询startDate到endDate之间的数据
    '''
    def queryAll(self, startDate='180701', endDate='180705'):
        
        dataDir = 'all_move_object'
        if not os.path.exists(dataDir):
            os.mkdir(dataDir)
        
        sql = "select distinct date_str " \
           "from ot_level2_his where date_str>='%s' and date_str<='%s'"%(startDate, endDate)

        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        
        print("total get %d days"%(len(rows)))
        for tdate in rows:
            self.getObjRecord(tdate[0])
            #break
            
if __name__ == '__main__':
    
    versionName = "version1"
    mr = MeteorRecord()
    mr.queryAll(startDate='181201', endDate='181231')
    mr.closeDb()
    
    