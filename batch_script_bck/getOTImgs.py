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
        
    def getOTImgsByDateStr(self, dateStr, dpath):
        
        rootPath = '/data/gwac_data'
        if not os.path.exists(dpath):
            os.makedirs(dpath)
        
        sql = "select ffc.store_path, ffc.file_name ot_sub_img, ffcr.file_name ot_sub_img_ref, ot2.look_back_result, ot2.ot_type " \
            "FROM fits_file_cut ffc " \
            "INNER JOIN ot_level2 ot2 on ot2.ot_id=ffc.ot_id " \
            "INNER JOIN fits_file2 ff on ff.ff_id=ffc.ff_id " \
            "INNER JOIN fits_file_cut_ref ffcr on ffcr.ot_id=ot2.ot_id and ffcr.success_cut=true " \
            "WHERE ot2.first_ff_number=ff.ff_number and ffc.success_cut=true and ot2.date_str='%s' " \
            "ORDER BY ot2.name "%(dateStr)
        
        print(sql)
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        
        listFile = "%s/list.txt"%(dpath)
        with open(listFile, 'w') as fp1:
            i = 0
            for trow in rows:
                tpath1 = trow[0]
                ot2Img = trow[1] + '.fit'
                ot2Diff = trow[1] + '_sub.fit'
                ot2Ref = trow[2] + '.fit'
                ot2LBR = trow[3]
                ot2Type = trow[4]
                
                ot2ImgP = "%s/%s/%s"%(rootPath, tpath1, ot2Img)
                ot2DiffP = "%s/%s/%s"%(rootPath, tpath1, ot2Diff)
                ot2RefP = "%s/%s/%s"%(rootPath, tpath1, ot2Ref)
                
                if os.path.exists(ot2ImgP) and os.path.exists(ot2DiffP) and os.path.exists(ot2RefP):
                    fp1.write("%s %s %s %s %d %d\n"%(tpath1, ot2Img, ot2Ref, ot2Diff, ot2LBR, ot2Type))
                    #shutil.copyfile(ot2ImgP,"%s/%s"%(dpath,ot2Img))
                    #shutil.copyfile(ot2DiffP,"%s/%s"%(dpath,ot2Diff))
                    #shutil.copyfile(ot2RefP,"%s/%s"%(dpath,ot2Ref))
                    i = i + 1
            print("total search record %d, with obj-tmp-diff exist %d\n"%(len(rows), i))
                
    
if __name__ == '__main__':
    
    dateStr = '180906'
    dpath = "/data/work/ot2_img_collection_%s_20180907"%(dateStr)
    mr = OTRecord()
    mr.getOTImgsByDateStr(dateStr, dpath)
    mr.closeDb()
    
    
