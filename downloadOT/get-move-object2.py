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
        
    def getObjRecord(self, movId, dateStr, totalFrame):
        
        sql = "select oorh1.date_ut, oorh1.ff_number, oorh1.x_temp, oorh1.y_temp, oorh1.ra_d, oorh1.dec_d, oorh1.mag_aper, oorh1.magerr_aper, oorh1.time_sub_second "\
            "from move_object_record mrec "\
            "INNER JOIN ot_observe_record_his oorh1 on  mrec.oor_id=oorh1.oor_id "\
            "WHERE mrec.mov_id=%s "\
            "ORDER BY oorh1.ff_number asc;"%(movId)

        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        f = open(r"all_move_object/%s_%d_%d.txt"%(dateStr, movId, totalFrame), "w")
        f.write("date_ut, frame_number, x_temp, y_temp, ra_d, dec_d, mag_aper,magerr_aper,seconds\n")
        for row in rows:
            f.write("%s, %d, %f, %f, %f, %f, %f, %f, %d\n"%row)
        f.close()
        cur.close()
                    
    '''
    *recNum: 最少记录条数
    *startDate-endDate: 从数据库查询startDate到endDate之间的数据
    '''
    def queryAll(self, recNum=20, startDate='180701', endDate='180702'):
        
        dataDir = 'all_move_object'
        if not os.path.exists(dataDir):
            os.mkdir(dataDir)
        
        sql = "select mov_id, date_str, total_frame_number " \
           "from move_object where mov_type = '1' AND frame_point_max_number = 1" \
           "and total_frame_number>=%d and date_str>='%s' and date_str<='%s'"%(recNum, startDate, endDate)

        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        
        print("total get %d moveObjects"%(len(rows)))
        for row in rows:
            self.getObjRecord(row[0],row[1],row[2])
            #break
        
            
if __name__ == '__main__':
    
    versionName = "version1"
    mr = MeteorRecord()
    mr.queryAll(recNum=50, startDate='190120', endDate='190120')
    mr.closeDb()
    
    