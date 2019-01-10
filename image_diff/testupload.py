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
            tpath = "%s\%s"%(path, tfname)
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

def testUpload():
    
    path=r"F:\test"
    fnames=['1.jpg','2.jpg','1.png','2.png']
    ftype="diffot1img"
    serverIP="http://127.0.0.1:8080"
    doUpload(path, fnames, ftype, serverIP)

if __name__ == "__main__":
    
    print(len(sys.argv))
    print(sys.argv)