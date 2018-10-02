# -*- coding: utf-8 -*-

import os
import psycopg2
import shutil
from astropy.io import fits
from gwac_util import zscale_image
import numpy as np

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
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
    
    def readfits(self, filename):
        rstdata = np.array([])
        try:
            with fits.open(filename,memmap=False) as ft:
                data = ft[0].data
                ft.close()
                data = data[40:61,40:61]
                rstdata = data
        except Exception as err:
            print("read %s error"%(filename))
            print(err)
        return rstdata
    
    def getOTImgs(self, dpath):
        
        rootPath = '/data/gwac_data'
        if not os.path.exists(dpath):
            os.makedirs(dpath)
        '''
        sql = "select ffc.store_path, ffc.file_name ot_sub_img, ffcr.file_name ot_sub_img_ref, " \
            "ot2.look_back_result, ot2.ot_type, ot2.name, ot2.date_str, oor.mag_aper mag, oor.magerr_aper magerr " \
            "FROM fits_file_cut_his ffc " \
            "INNER JOIN ot_level2_his ot2 on ot2.ot_id=ffc.ot_id " \
            "INNER JOIN fits_file2_his ff on ff.ff_id=ffc.ff_id " \
            "INNER JOIN ot_observe_record_his oor on oor.ffc_id>0 and oor.ffc_id=ffc.ffc_id " \
            "INNER JOIN fits_file_cut_ref ffcr on ffcr.ot_id=ot2.ot_id and ffcr.success_cut=true " \
            "WHERE ot2.first_ff_number=ff.ff_number and ffc.success_cut=true " \
            "ORDER BY ot2.name "
         '''   
        sql = "select ffc.store_path, ffc.file_name ot_sub_img, ffcr.file_name ot_sub_img_ref, " \
            "ot2.look_back_result, ot2.ot_type, ot2.name, ot2.date_str, oor.mag_aper mag, oor.magerr_aper magerr " \
            "FROM fits_file_cut ffc " \
            "INNER JOIN ot_level2 ot2 on ot2.ot_id=ffc.ot_id " \
            "INNER JOIN fits_file2 ff on ff.ff_id=ffc.ff_id " \
            "INNER JOIN ot_observe_record oor on oor.ffc_id>0 and oor.ffc_id=ffc.ffc_id " \
            "INNER JOIN fits_file_cut_ref ffcr on ffcr.ot_id=ot2.ot_id and ffcr.success_cut=true " \
            "WHERE ot2.first_ff_number=ff.ff_number and ffc.success_cut=true " \
            "ORDER BY ot2.name "
        
        print(sql)
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        print("total read record %d"%(len(rows)))
        
        timgs = []
        props = []
        i = 1
        for trow in rows:
            tpath1 = trow[0]
            ot2Img = trow[1] + '.fit'
            ot2Diff = trow[1] + '_sub.fit'
            ot2Ref = trow[2] + '.fit'
            ot2LBR = trow[3]
            ot2Type = trow[4]
            ot2Name = trow[5]
            ot2Date = trow[6]
            ot2Mag = trow[7]
            ot2MagErr = trow[8]
            
            ot2ImgP = "%s/%s/%s"%(rootPath, tpath1, ot2Img)
            ot2DiffP = "%s/%s/%s"%(rootPath, tpath1, ot2Diff)
            ot2RefP = "%s/%s/%s"%(rootPath, tpath1, ot2Ref)
            
            if os.path.exists(ot2ImgP) and os.path.exists(ot2DiffP) and os.path.exists(ot2RefP) and ot2MagErr>0:
                #if i>180000:
                objImg = self.readfits(ot2ImgP)
                refImg = self.readfits(ot2RefP)
                diffImg = self.readfits(ot2DiffP)
                if objImg.shape[0]==0:
                    continue
                if refImg.shape[0]==0:
                    continue
                if diffImg.shape[0]==0:
                    continue
                        
                timgs.append([objImg, refImg, diffImg])
                props.append([ot2Name, ot2Img, ot2Ref, ot2Diff, ot2LBR, ot2Type, ot2Date, ot2Mag, 1.087/ot2MagErr])
                if i%500 == 0:
                    print("process %d images"%(i))
            
                if i%10000 == 0:
                    timgs =  np.array(timgs)
                    props =  np.array(props)
                    binFile = "%s/GWAC_OT_ALL_%07d.npz"%(dpath,i)
                    np.savez_compressed(binFile, imgs=timgs, props=props)
                    print("save %s"%(binFile))
                    timgs = []
                    props = []
                    #break
                
                i = i + 1
        
        timgs =  np.array(timgs)
        props =  np.array(props)
        binFile = "%s/GWAC_OT_ALL_%07d.npz"%(dpath,i)
        np.savez_compressed(binFile, imgs=timgs, props=props)
        print("total search record %d, with obj-tmp-diff exist %d\n"%(len(rows), i))
        
    
if __name__ == '__main__':
    
    dateStr = '180906'
    dpath = "/data/work/ot2_img_collection_20181001"
    mr = OTRecord()
    mr.getOTImgs(dpath)
    mr.closeDb()
    
    