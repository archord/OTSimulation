# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import os
import psycopg2


class CatalogList:
    
    connParam={
        "host": "10.0.82.111",
        "port": "5432",
        "dbname": "gwac",
        "user": "postgres",
        "password": "gwac1234"
        }
    
    def __init__(self):
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
    
    def reProcessAll(self):
        sql="update object_catalog set is_process=false"
        cur = self.conn.cursor()
        cur.execute(sql)
        cur.close()
        
    def getRecord(self):
        
        sql = "select objCat.oc_id, objCat.name, objCat.path, objCat.date_ut, objCat.cam_name, objCat.sky_name, tmpCat.name tmpName, tmpCat.path tmpPath "\
            "from object_catalog objCat "\
            "INNER JOIN template_catalog tmpCat on objCat.tc_id=tmpCat.tc_id "\
            "where objCat.is_upload=true and objCat.is_process=false "\
            "ORDER BY objCat.date_ut asc "\
            "limit 20"

        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        for trow in rows:
            print(trow)
            objCatId = trow[0]
            tsql = "update object_catalog set is_process=true where oc_id=%d"%(objCatId)
            print(tsql)
            cur.execute(tsql)
            self.conn.commit()
            
        cur.close()
        

            
if __name__ == '__main__':
    
    versionName = "version1"
    mr = CatalogList()
    mr.getRecord()
    mr.closeDb()
    
    