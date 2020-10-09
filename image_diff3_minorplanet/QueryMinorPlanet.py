# -*- coding: utf-8 -*-
import numpy as np
import pymysql
import math
import matplotlib.pyplot as plt

def getGreatCircleDistance(ra1, dec1, ra2, dec2):
    rst = 57.295779513 * math.acos(math.sin(0.017453293 * dec1) * math.sin(0.017453293 * dec2)
            + math.cos(0.017453293 * dec1) * math.cos(0.017453293 * dec2) * math.cos(0.017453293 * (math.fabs(ra1 - ra2))));
    return rst


def calSearchBox(ra, dec, searchRadius):

    flag = 0
    if ra > 360.0 or ra < 0.0 or dec > 90.0 or dec < -90.0 or searchRadius > 20.0:
      return flag
    else:
      minDec = dec - searchRadius;
      maxDec = dec + searchRadius;
      if (maxDec > 90.0):
        maxDec = 90
      if (minDec < -90.0):
        minDec = -90

      if math.fabs(maxDec) > math.fabs(minDec):
          tDec = math.fabs(maxDec)
      else:
          tDec = math.fabs(minDec)
          
      cosd = math.cos(tDec * 0.0174532925)
      if (cosd > searchRadius / 180.0):
        maxRa = (ra + searchRadius / cosd + 360.0) % 360.0
        minRa = (ra - searchRadius / cosd + 360.0) % 360.0
      else:
        maxRa = 360
        minRa = 0
      if minRa > maxRa:
        flag = 2
      else:
        flag = 1
      return flag, minDec, maxDec, minRa, maxRa

      
#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class QueryMinorPlanet:
    
    connParam={
        "host": "172.28.8.100",
        "port": "3306",
        "dbname": "nomad_catalogue",
        "user": "catauser",
        "password": "catauseradmin"
        }
    
    def __init__(self):
        
        self.conn = False
        self.conn2 = False
        self.dateStr = ''
        
    def connDb(self):
        
        self.conn = pymysql.connect("172.28.8.100","catauser","catauseradmin","catalogue" )
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
    
    def getMaxAbsValue(self, tableName, name, maxMag):

        val = 19.9;
        sql = "select max(abs(%s)) from %s where VMAG<%f and abs(%s)<20;"%(name, tableName, maxMag, name)
        try:
            #self.connDb()
            #print(sql)
            cur = self.conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            val = rows[0][0]
            #cur.close()
            #self.closeDb()
        except Exception as err:
            print(" query OT2 image error ")
            print(err)
        return val


    def matchMP(self, ra, dec, dateStr, obsUtc, searchRadius=0.05, mag=16.0):

        if self.dateStr!=dateStr:
            self.dateStr=dateStr
            self.tableName = "aoop_longlat_20%s"%(dateStr) #yyyyMMdd
            #print("minor planet table name=%s"%(self.tableName))
            self.maxRaSpeed = self.getMaxAbsValue(self.tableName, "DLON", mag)
            #print("minor planet self.maxRaSpeed=%f"%(self.maxRaSpeed))
            self.maxDecSpeed = self.getMaxAbsValue(self.tableName, "DLAT", mag)
            #print("minor planet self.maxDecSpeed=%f"%(self.maxDecSpeed))
            if (self.maxRaSpeed > 20):
              self.maxRaSpeed = 19.9
            if (self.maxDecSpeed > 20):
              self.maxDecSpeed = 19.9
              
            self.maxSpeed = self.maxRaSpeed
            if self.maxSpeed<self.maxDecSpeed:
                self.maxSpeed=self.maxDecSpeed
    
        tflag1, minDec1, maxDec1, minRa1, maxRa1 = calSearchBox(ra, dec, self.maxSpeed + searchRadius)
        
        minDis = searchRadius
        tmag = 0
        if tflag1 != 0:
          sql = "select * from %s where VMAG<%f "%(self.tableName, mag)
          if tflag1 == 1:
            sql = " %s and LON between %f and %f "%(sql, minRa1, maxRa1)
          else:
            sql = " %s and ( LON > %f or LON <%f) "%(sql, minRa1, maxRa1)
          
          sql = " %s and LAT between %f and %f "%(sql, minDec1, maxDec1)
          
          print(sql)
          
          #self.connDb()
          cur = self.conn.cursor()
          cur.execute(sql)
          rows = cur.fetchall()
          #cur.close()
          #self.closeDb()
          
          #obsUtc = "%sT%s"%(dateObs, timeObs)
          ttime = obsUtc.split('T')
          hms=ttime[1].split(':')
          subDay = float(hms[0])/24 + float(hms[1])/24/60 + float(hms[2])/24/60/60
          print("minor planet (%f, %f) %s subDay=%f"%(ra, dec, obsUtc, subDay))
          
          for td in rows:
              print(td)
              ra1=td[3]
              dec1=td[4]
              raSpeed=td[5]
              decSpeed=td[6]
              mag = td[7]
              preRa = ra1 + raSpeed * subDay/math.cos(dec1*0.017453293)
              preDec = dec1 + decSpeed * subDay
              tDis = getGreatCircleDistance(ra, dec, preRa, preDec)
              print(tDis)
              if tDis<minDis:
                  minDis = tDis
                  tmag = mag

        return minDis, tmag
    
if __name__ == '__main__':
    
    ra = 205.327
    dec = 2.797465
    dateStr =  '200130'
    obsUtc = '2020-01-30T19:09:05'
    
    tquery = QueryMinorPlanet()
    tquery.connDb()
    rows = tquery.matchMP(ra, dec, dateStr, obsUtc, searchRadius=0.05, mag=16.0)
    tquery.closeDb()
    print(rows)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    