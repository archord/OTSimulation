# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import time
import logging
import os
import math
from astropy.wcs import WCS
from datetime import datetime
import traceback
import matplotlib.pyplot as plt
import warnings
from astropy.modeling import models, fitting

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class GWACWCSIndex:
    
    orgImgRoot = '/data/gwac_data/gwac_orig_fits'
    wcsIdxRoot = '/data/gwac_data/gwac_wcs_idx'
    webServerIP1 = '172.28.8.28:8080'
    webServerIP2 = '10.0.10.236:9995'
    
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
        
        self.imgSize = (4136, 4096)
        self.templateImg = 'ti.fit'
        self.tmpRoot="/dev/shm/gwacWCS"
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        if not os.path.exists(self.templateDir):
            os.system("mkdir -p %s"%(self.templateDir))
         
    
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam3)
        
    def closeDb(self):
        self.conn.close()
        
    def getDataFromDB(self, sql):
                
        tsql = sql
        #self.log.debug(tsql)
        
        try:
            self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(tsql)
            rows = cur.fetchall()
            cur.close()
            self.closeDb()
        except Exception as err:
            rows = []
            print(" query data error ")
            print(err)
            
        return np.array(rows)
    
    def queryObs(self, size=10):
    
        tsql = "select center_ra, center_dec, left_top_ra, left_top_dec, left_bottom_ra, left_bottom_dec, "\
                "right_top_ra, right_top_dec, right_bottom_ra, right_bottom_dec "\
                "from observation_record_statistic "\
                "where has_wcs=true and start_obs_time is not null "\
                "ORDER BY ors_id desc limit %d"%(size)
        #print(tsql)
        return self.getDataFromDB(tsql)
    
    def wcs2plane(self, raD,decD, raD0, decD0):
        
        D2R = math.pi/180.0
        ra0 =  raD0*D2R
        dec0 = decD0*D2R
        ra =  raD*D2R
        dec = decD*D2R
        
        j = 0
        tiny = 1e-6;

        sdec0 = math.sin(dec0);
        sdec = math.sin(dec);
        cdec0 = math.cos(dec0);
        cdec = math.cos(dec);
        radif = ra - ra0;
        sradif = math.sin(radif);
        cradif = math.cos(radif);
    
        denom = sdec * sdec0 + cdec * cdec0*cradif;
    
        if denom > tiny:
            j = 0
        elif denom >= 0.0:
            j = 1
            denom = tiny
        elif denom > -tiny:
            j = 2
            denom = -tiny;
        else:
            j = 3
    
        xi = cdec * sradif / denom;
        eta = (sdec * cdec0 - cdec * sdec0 * cradif) / denom;
    
        return xi, eta, j
        
    '''
    
        tsql = "update observation_record_statistic set center_ra=%f, center_dec=%f, " \
            "left_top_ra=%f, left_top_dec=%f, left_bottom_ra=%f, left_bottom_dec=%f, "\
            "right_top_ra=%f, right_top_dec=%f, right_bottom_ra=%f, right_bottom_dec=%f where ors_id=%s" \
            %(rd[0][0], rd[0][1], rd[1][0], rd[1][1], rd[2][0], rd[2][1], rd[3][0], rd[3][1],rd[4][0], rd[4][1], orsId)
                tXYs.append((width/2,height/2))
                tXYs.append((0,0))
                tXYs.append((0,height-1))
                tXYs.append((width-1,height-1))
                tXYs.append((width-1,0))
                '''
                
    def polynomialFit(self, dataOi, dataTi, degree=3):
            
        oix = dataOi[:,0]
        oiy = dataOi[:,1]
        tix = dataTi[:,0]
        tiy = dataTi[:,1]
        
        p_init = models.Polynomial2D(degree)
        fit_p = fitting.LevMarLSQFitter()
        
        with warnings.catch_warnings():
            # Ignore model linearity warning from the fitter
            warnings.simplefilter('ignore')
            tixp = fit_p(p_init, oix, oiy, tix)
            tiyp = fit_p(p_init, oix, oiy, tiy)
            
        return tixp, tiyp
        
    def planProject(self):
        
        width = 4096
        height = 4136
        imgXY = []
        imgXY.append((width/2,height/2))
        imgXY.append((0,0))
        imgXY.append((0,height-1))
        imgXY.append((width-1,height-1))
        imgXY.append((width-1,0))
        imgXY = np.array(imgXY)
        
        tdatas = self.queryObs()
        #print(tdatas)
        for td in tdatas:
            transXY = []
            print(td)
            xi, eta, j = self.wcs2plane(td[0],td[1], td[0],td[1])
            transXY.append((xi,eta))
            print(xi, eta, j)
            xi, eta, j = self.wcs2plane(td[2],td[3], td[0],td[1])
            transXY.append((xi,eta))
            print(xi, eta, j)
            xi, eta, j = self.wcs2plane(td[4],td[5], td[0],td[1])
            transXY.append((xi,eta))
            print(xi, eta, j)
            xi, eta, j = self.wcs2plane(td[6],td[7], td[0],td[1])
            transXY.append((xi,eta))
            print(xi, eta, j)
            xi, eta, j = self.wcs2plane(td[8],td[9], td[0],td[1])
            transXY.append((xi,eta))
            print(xi, eta, j)
            transXY=np.array(transXY)
            
            tra = (td[8]+td[6])/2
            tdec = (td[9]+td[7])/2
            print(tra, tdec)
            txi, teta, j = self.wcs2plane(tra,tdec, td[0],td[1])
            print(xi, eta, j)
            
            #convexHull
            tixp, tiyp = self.polynomialFit(transXY, imgXY, 1)
            timgX = tixp(txi, teta)
            timgY = tiyp(txi, teta)
            print("imgx=%f, imgy=%f"%(timgX, timgY))
            
            fig = plt.figure()
            plt.plot(transXY[:,0], transXY[:,1])
            plt.plot(xi,eta, marker='o', color='r', ls='')
            plt.plot(txi,teta, marker='o', color='b', ls='')
            plt.show()
            #break

if __name__ == '__main__':
    
    wcsIdx = GWACWCSIndex()
    wcsIdx.planProject()