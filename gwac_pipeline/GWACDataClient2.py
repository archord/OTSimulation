# -*- coding:utf-8 -*-
import zmq
import os
from astropy.time import Time
from astropy.io import fits


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
		print("summary %s"%(summary))
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
    

def main():
    tpath = "data"
    gdc = GWACDataClient('10.0.82.111', '12626')
    tfiles = os.listdir(tpath)
    tfiles.sort()
    tcats = []
    tmpCat = ""
    for tfile in tfiles:
        if tfile.find("Fcat")>-1:
            if tfile.find("Temp")>-1:
                tmpCat = tfile
            else:
                tcats.append(tfile)
    
    for i, tcat in enumerate(tcats):
        if i == 0 and len(tmpCat)>0:
            gdc.send(tpath, tcat, tmpCat)
        else:
            gdc.send(tpath, tcat, "")
        
        print("*************%dth send done\n"%(i+1))
        if i>2:
            break

if __name__ == '__main__':
	main()

