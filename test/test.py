# -*- coding: utf-8 -*-
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class QueryData:
    
    connParam={
        "host": "192.168.56.102",
        "port": "5432",
        "dbname": "objectanalyze",
        "user": "postgres",
        "password": "xyag902"
        }
    
    def __init__(self):
        
        self.conn = False
        self.conn2 = False
        
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam)
        self.dataVersion = ()
        
    def closeDb(self):
        self.conn.close()
        
    def insertData(self,name,status,name1,name2,orbit):
        
        sql = "insert into object(obj_name,status,name1,name2,orbit_info) "\
            "values('%s','%s','%s','%s','%s');"%(name,status,name1,name2,orbit)
        print(sql)
        try:
            #self.connDb()
    
            cur = self.conn.cursor()
            cur.execute(sql)
            #cur.close()
            #cur.commit()
            #self.closeDb()
        except Exception as err:
            print(" insert data error ")
            print(err)
            
    

if __name__ == '__main__':
    
    dataFile = 'e:/resource/objectList.txt'
    #tquery = QueryData()
    #tquery.connDb()
    
    fo = open(dataFile, "r")
    lines = fo.readlines()
    fo.close()
    
    content = ''
    for line in lines:
        content = content + line
        
    
    pageContent = BeautifulSoup(content, 'html.parser')
    trs = pageContent.findAll("tr")
    
    for tr in trs:
        tds = tr.findAll('td')
        if len(tds)==9:
            '''
            name = str(tds[1].find('a').contents[0])
            status = str(tds[2].find('span').contents[0])
            name1 = str(tds[3].find('span').contents[0])
            name2 = str(tds[4].contents[0])
            orbit = str(tds[5].find('a').contents[0])
            '''
            name = str(tds[1].find('a').contents[0])
            status = str(tds[2].find('span').contents[0])
            name1 = str(tds[3].find('span').contents[0])
            name2 = str(tds[4].contents[0])
            orbit = str(tds[5].find('a').contents[0])
            '''
            print(name)
            print(status)
            print(name1)
            print(name2)
            print(orbit)
            print(type(name))'''
            #tquery.insertData(name,status,name1,name2,orbit)
            
            sql = "insert into object(obj_name,status,name1,name2,orbit_info) "\
                "values('%s','%s','%s','%s','%s');"%(name,status,name1,name2,orbit)
            print(sql)
            #break
    #tquery.closeDb()
    