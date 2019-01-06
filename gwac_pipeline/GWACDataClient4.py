# -*- coding:utf-8 -*-
import zmq
import os
from astropy.time import Time
from astropy.io import fits
import thread  
import time


class GWACDataClient(object):
        def __init__(self, ip, port, tryTimes = 3):
                super(GWACDataClient, self).__init__()
                self.ip = ip
                self.port = str(port)
                self.tryTimes = tryTimes

                context = zmq.Context()
                self.socket =  context.socket(zmq.REQ)
                try:
                        addr = "tcp://%(ip)s:%(port)s" % { 'ip' : self.ip, 'port' : self.port }
                        print(addr)
                        self.socket.connect(addr)
                except Exception as e:
                        self.reportError("init error " + addr)
                finally:
                        pass
                print('connected to %(addr)s server' % { 'addr' : addr})

        def reportError(self, msg):
                print(str(msg))
                
        def sendMsg(self, msg):
                tryTimes = self.tryTimes
                while tryTimes > 0:
                        try:
                                self.socket.send(msg)
                                message = self.socket.recv()
                                if message == "yes!":
                                    print("receive success")
                        except Exception as e:
                                self.reportError(e)
                                tryTimes -= 1
                        return True
                self.reportError(msg+" failed to send")
                return False
                
        def sendFile(self, filename):
                fp = None
                try:
                        fp = open(filename, 'rb')
                        content = fp.read()
                        return self.sendMsg(content)
                except Exception as e:
                        self.reportError(e)
                        if fp:
                                fp.close()
                else:
                        fp.close()
                return True

        def getHeaders(self, filename):
                ccdNo = ''
                fieldNo = ''
                timeStamp = ''
                with fits.open(filename,memmap=False) as ft:
                        ccdNo = ft[0].header['CAM_ID']
                        fieldNo = ft[0].header['FIELDID']
                        jd = ft[0].header['JD']
                        timeStamp = Time(float(jd), format='jd').iso
                return ccdNo, fieldNo, timeStamp

        def send(self, tpath, objCat, tempCat=""):
                # summary是摘要信息，以'\n'分格，第一个字符串分别为两个发送的文件，filenameList是包含要发送的文件名

                objPath = "%s/%s"%(tpath, objCat)
                tempPath = "%s/%s"%(tpath, tempCat)

                if len(objCat)>0:
                        ccdNoo, fieldNoo, timeStampo = self.getHeaders(objPath)
                else:
                        print("must send objCat")
                        return False

                if len(tempCat)>0:
                        ccdNot, fieldNot, timeStampt = self.getHeaders(tempPath)
                        summary = "%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s"%(tempCat,ccdNot, fieldNot, timeStampt,objCat,ccdNoo, fieldNoo, timeStampo)
                else:
                        summary = "%s\n%s\n%s\n%s"%(objCat,ccdNoo, fieldNoo, timeStampo)
                print("*****************startSend:\nsummary %s"%(summary))
                ret = self.sendMsg(summary)
                if ret:
                        if len(tempCat)>0:
                                trst = self.sendFile(tempPath)
                                print("send %s, %s"%(tempCat, trst))
                        trst = self.sendFile(objPath)
                        print("send %s, %s"%(tempCat, trst))
                else:
                        print("send summary error, stop send file")
                        return False
                return True

class T_O:
        def __init__(self,t):
                self.OFile = [] 
                self.Temp = t   
	def setTemp(self,Temp):
		self.Temp = Temp
	def addfile(self,file):
		self.OFile.append(file)
	
class device:
        def __init__(self,name):
                self.T_Os = []
                self.name = name
	def add_T_O(self,temp):
		to = T_O(temp)
		self.T_Os.append(to)
        def getlen():
                return len(T_Os)


	
def txt_wrap_by(start_str, end, html):
        start = html.find(start_str)
        #if start >= 0:
        start += len(start_str)
        end = html.find(end, start)
           # if end >= 0:
        return html[start:end]


def sendDir(tpath):
    print("start send data from %s"%(tpath))
    #tpath = "data"
    gdc = GWACDataClient('10.0.82.111', '12626')
    tfiles = os.listdir(tpath)
    tfiles.sort()
    tcats = []
    tmpCat = ""
    dev = device(tpath)
    for tfile in tfiles:
        if tfile.find("Temp")>-1:
           dev.add_T_O(tfile)
    print(len(dev.T_Os))
    for temp in dev.T_Os:
        start = temp.Temp.find("_")
        end = temp.Temp.find(".")
        tempname = temp.Temp[start+1:end]
        #print(tempname)
        for tfile in tfiles:
            start = tfile.find("-")
            end = tfile.find("_")
            end = tfile.find("_",end+1)
            otable = tfile[start+1:end]
            if otable == tempname:
                temp.addfile(tfile)
        print(len(temp.OFile)) 
        #print("!!!!!"+tempname+"???"+tfile+"!!!!!")

    for temp in dev.T_Os:
        mutex.acquire()
        gdc.send(tpath, temp.OFile[0] , temp.Temp)
        mutex.release()
       # mutex.acquire()
        for i,val in enumerate(temp.OFile):
            mutex.acquire()
            if i == 0:
               pass
            else:
               gdc.send(tpath, val, "")
               print("*************%dth send done\n"%(i+1))
            mutex.release()
            #if i > 0 and i < 3:   
            time.sleep(15)
            #if i>2:
            #    break
        #mutex.release()
        #time.sleep(15)
    else:
        print("cannot find template file")


if __name__ == '__main__':

    gdc = GWACDataClient('10.0.82.111', '12626')
    gdc.sendMsg("reset")
    time.sleep(2)
    gdc.sendMsg("start")

    mutex = thread.allocate_lock()
    rootPath='data3'


    tdirs = os.listdir(rootPath)
    tdirs.sort()
  
    tdirs2 = []
    for tdir in tdirs:
        if tdir[0]=='0' and len(tdir)==3:
            tdirs2.append(tdir)
    
    for tdir2 in tdirs2:
        tpath2 = "%s/%s"%(rootPath, tdir2)
        thread.start_new_thread(sendDir, (tpath2,))
        #break
while True:
    time.sleep(10)

                
