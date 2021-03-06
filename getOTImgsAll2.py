# -*- coding: utf-8 -*-
#12像素，FOT观测假OT2，TOT小辛图像, 减背景和不减背景
from astropy.io import fits
import numpy as np
import os
import psycopg2


#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class OTRecord:
    
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
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def connDb2(self):
        self.conn2 = psycopg2.connect(**self.connParam3)
        
    def closeDb2(self):
        self.conn2.close()
    
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
        
    def updateOT2LookBackCNN(self, ot2Name, rst):
        
        try:
            
            sql = "update ot_level2 set look_back_cnn=%f where name='%s'"%(rst, ot2Name)
            #print(sql)
            conn = psycopg2.connect(**self.connParam2)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
            
            conn.close()
        except Exception as err:
            print(" update OT2 %s error "%(ot2Name))
            print(err)
        
    
    def getOTImgs(self):
        
        
        timgs =  np.array([])
        props =  np.array([])
        
        try:
            self.connDb()
            
            rootPath = '/data/gwac_data' 
            sql = "select ffc.store_path, ffc.file_name ot_sub_img, ffcr.file_name ot_sub_img_ref, " \
                "ot2.look_back_result, ot2.ot_type, ot2.name, ot2.date_str, oor.mag_aper mag, oor.magerr_aper magerr " \
                "FROM fits_file_cut ffc " \
                "INNER JOIN ot_level2 ot2 on ot2.ot_id=ffc.ot_id and ot2.look_back_cnn<0 " \
                "INNER JOIN ot_observe_record oor on oor.ot_id=ot2.ot_id and oor.ff_number=ot2.first_ff_number " \
                "INNER JOIN fits_file_cut_ref ffcr on ffcr.ot_id=ot2.ot_id and ffcr.success_cut=true " \
                "WHERE ot2.first_ff_number=ffc.number and ffc.success_cut=true " \
                "ORDER BY ot2.name"
            #    "ORDER BY ot2.name limit 100"
            
            cur = self.conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            
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
                    if objImg.shape[0]>0 and refImg.shape[0]>0 and diffImg.shape[0]>0: 
                        timgs.append([objImg, refImg, diffImg])
                        props.append([ot2Name, ot2Img, ot2Ref, ot2Diff, ot2LBR, ot2Type, ot2Date, ot2Mag, 1.087/ot2MagErr])

                    i = i + 1
            
            timgs =  np.array(timgs)
            props =  np.array(props)
            
            self.closeDb()
        except Exception as err:
            print(" query OT2 image error ")
            print(err)
        
        return timgs, props


    def getHisOTImgs(self, dpath, dateStr):
        
        if not os.path.exists(dpath):
            os.makedirs(dpath)
        
        timgs =  np.array([])
        props =  np.array([])
        
        try:
            self.connDb2()
            
            rootPath = '/data/gwac_data' 
            sql = "select ffc.store_path, ffc.file_name ot_sub_img, ffcr.file_name ot_sub_img_ref, " \
                "ot2.look_back_result, ot2.ot_type, ot2.name, ot2.date_str, oor.mag_aper mag, oor.magerr_aper magerr " \
                "FROM fits_file_cut_his ffc " \
                "INNER JOIN ot_level2_his ot2 on ot2.ot_id=ffc.ot_id and ot2.date_str='"+dateStr+"' " \
                "INNER JOIN ot_observe_record_his oor on oor.ot_id=ot2.ot_id and oor.ff_number=ot2.first_ff_number " \
                "INNER JOIN fits_file_cut_ref_his ffcr on ffcr.ot_id=ot2.ot_id and ffcr.success_cut=true " \
                "WHERE ot2.first_ff_number=ffc.number and ffc.success_cut=true " \
                "ORDER BY ot2.name limit 100"
            
            cur = self.conn2.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
            print("sql query %d rows"%(len(rows)))
            
            timgs = []
            props = []
            i = 0
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
                    if objImg.shape[0]>0 and refImg.shape[0]>0 and diffImg.shape[0]>0: 
                        timgs.append([objImg, refImg, diffImg])
                        props.append([ot2Name, ot2Img, ot2Ref, ot2Diff, ot2LBR, ot2Type, ot2Date, ot2Mag, 1.087/ot2MagErr])
                        i = i + 1
                    else:
                        print("read image error")
                else:
                    print("******************************")
                    if not os.path.exists(ot2ImgP):
                        print("%s not exist"%(ot2ImgP))
                    if not os.path.exists(ot2DiffP):
                        print("%s not exist"%(ot2DiffP))
                    if not os.path.exists(ot2RefP):
                        print("%s not exist"%(ot2RefP))
                    if ot2MagErr<=0:
                        print("%s, ot2MagErr error: %f "%(ot2Name, ot2MagErr))
            
            timgs =  np.array(timgs)
            props =  np.array(props)
            
            #binFile = "%s/GWAC_OT_ALL_%07d.npz"%(dpath,i)
            #np.savez_compressed(binFile, imgs=timgs, props=props)
            #print("total search record %d, with obj-tmp-diff exist %d\n"%(len(rows), i))
            
            self.closeDb2()
        except Exception as err:
            print(" query OT2 image error ")
            print(err)
        
        return timgs, props


if __name__ == '__main__':
    
    dateStr = '181011'
    dpath = "/data/work/ot2_img_collection_%s"%(dateStr)
    mr = OTRecord()
    mr.getHisOTImgs(dpath, dateStr)
