# -*- coding: utf-8 -*-
import os
import traceback
import time
import requests
from datetime import datetime, timedelta

def sendMsg(tmsg):

    try:
        sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        tmsg = "%s: %s"%(sendTime, tmsg)
        msgURL = "http://172.28.8.8:8080/gwebend/sendTrigger2WChart.action?chatId=gwac004&triggerMsg="
        turl = "%s%s"%(msgURL,tmsg)
        msgSession = requests.Session()
        msgSession.get(turl, timeout=10, verify=False)
    except Exception as e:
        print(str(e))
        
def fpackDir(root, dateStr, ccd):
    
    try:
        fpackEXE = '/data/work/program/image_diff/tools/cfitsio/fpack'
        fullpath = "%s/%s/%s"%(root,dateStr,ccd)
        tfiles = os.listdir(fullpath)
        tfiles.sort()
        
        fits = []
        for tfile in tfiles: 
            if tfile[-4:]=='.fit':
                fits.append(tfile)
    
        if len(fits)>0:
            print(fullpath)
            
        fpackNum=0
        for tfit in fits:
            print(tfit)
            tpath00 = "%s/%s"%(fullpath,tfit)
            os.system("%s -D %s"%(fpackEXE, tpath00))
            fpackNum = fpackNum + 1
        
        if len(fits)>0:
            tstr = '%s %s total %d, fit %d, fpack %d'%(dateStr, ccd, len(tfiles), len(fits), fpackNum)
            sendMsg(tstr)
    except Exception as e:
        print(str(e))
        traceback.print_exception()
        
if __name__ == '__main__':
    
    root = '/data/gwac_data/gwac_orig_fits'
    dateStrs = os.listdir(root)
    dateStrs.sort()
    for tdate in dateStrs:
        datePath = "%s/%s"%(root,tdate)
        ccds = os.listdir(datePath)
        ccds.sort()
        for tccd in ccds:
            fpackDir(root, tdate, tccd)
