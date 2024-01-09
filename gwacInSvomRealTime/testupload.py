# -*- coding: utf-8 -*-
import sys
import requests
import traceback
from datetime import datetime

def doUpload(path, fnames, ftype, serverIP):
    
    try:
        turl = "%s/gwebend/commonFileUpload.action"%(serverIP)
        
        sendTime = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
        values = {'fileType': ftype, 'sendTime': sendTime}
        files = []
        for tfname in fnames:
            tpath = "%s/%s"%(path, tfname)
            files.append(('fileUpload', (tfname,  open(tpath,'rb'), 'text/plain')))
        
        #files = {'fileUpload': ('report.xls', open('F:\\test\\2.jpg', 'rb'), 'text/plain')}
        print(values)
        print(files)
        msgSession = requests.Session()
        r = msgSession.post(turl, files=files, data=values)
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)

#上传图像参数
def testUpload1():
    
    path="gwacInSvomRealTime"
    fnames=['G022_Mon_objt_240107T10594733.imqty']
    ftype="imqty"
    serverIP="http://10.0.10.236:8080"
    doUpload(path, fnames, ftype, serverIP)


#上传图像参数
def testUpload2():
    
    path="/Users/xy/work/python/OTSimulation/gwacInSvomRealTime"
    #上传的jpg文件以preview作为后缀G044_Mon_objt_231208T10110750_preview.jpg
    fnames=['G101_Mon_objt_231208T10110750_preview.jpg']
    ftype="impre"
    serverIP="http://172.28.8.8:8080"
    doUpload(path, fnames, ftype, serverIP)

if __name__ == "__main__":
    
    print(len(sys.argv))
    print(sys.argv)
    testUpload1()