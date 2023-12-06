# -*- coding: utf-8 -*-

import os
import psycopg2
import shutil


class OTRecord:
    
    connParam={
        "host": "10.0.3.62",
        "port": "5433",
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
    
    def __init__(self):
        
        self.conn = psycopg2.connect(**self.connParam2)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def getFitsByTypeId(self, typeId, dpath, tableName):
        
        rootPath = '/data/gwac_data'
        dpath0 = '%s/%d'%(dpath, typeId)
        if not os.path.exists(dpath0):
            os.makedirs(dpath0)
        
        sql = "select ffc.store_path, ffc.file_name "\
            "FROM %s ffc "\
            "INNER JOIN ot_level2_his ot2 on ot2.ot_id=ffc.ot_id and ot2.ot_type=%d "\
            "WHERE ffc.success_cut=true;"%(tableName, typeId)
        #print(sql)
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        
        for trow in rows:
            spath1 = "%s/%s/%s.fit"%(rootPath, trow[0], trow[1])
            dpath1 = "%s/%s.fit"%(dpath0, trow[1])
            #print(spath1)
            #break
            if os.path.exists(spath1):
                shutil.copyfile(spath1,dpath1)
                
    
if __name__ == '__main__':
    
    dpath = "/data/work/ot_classify"
    otTypeList = [11,15,13,16,12,8	,18,5	,17,4	,3	,6	,7	,1]
    table1 = 'fits_file_cut_ref'
    table2 = 'fits_file_cut_his'
    mr = OTRecord()
    for ttpye in otTypeList:
        print("start process %d"%(ttpye))
        mr.getFitsByTypeId(ttpye, dpath, table1)
        mr.getFitsByTypeId(ttpye, dpath, table2)
        #break
    mr.closeDb()
    
    
