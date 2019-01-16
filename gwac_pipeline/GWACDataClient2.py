# -*- coding:utf-8 -*-
import zmq
import os
from astropy.time import Time
from astropy.io import fits
import traceback
import paramiko
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
                self.socket.send_string(msg)
                message = self.socket.recv()
                if message == "yes!":
                    return True
            except Exception as e:
                self.reportError(e)
                tryTimes -= 1
            return True
        self.reportError(msg+" failed to send")
        return False
    
    def sendFile_(self, msg):
        tryTimes = self.tryTimes
        while tryTimes > 0:
            try:
                self.socket.send(msg)
                message = self.socket.recv()
                if message == "yes!":
                    return True
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
            return self.sendFile_(content)
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
        tempPath = ''
        jd = ''
        
        try:
            with fits.open(filename,memmap=False) as ft:
                ccdNo = ft[0].header['CAM_ID']
                fieldNo = ft[0].header['FIELDID']
                jd = ft[0].header['JD']
                tempPath = ft[0].header['TEMPNA']
                timeStamp = Time(float(jd), format='jd').iso
        except Exception as e:
            print(e)
        return ccdNo, fieldNo, timeStamp, tempPath, jd
    
    #JD, GRID_ID, FIELD_ID, UNIT_ID, CAM_ID, TEMPNA
    def getHeaders2(self, filename):
        unitID = ''
        camID = ''
        gridID = ''
        fieldID = ''
        jd = ''
        
        try:
            with fits.open(filename,memmap=False) as ft:
                unitID = ft[0].header['UNIT_ID']
                camID = ft[0].header['CAM_ID']
                gridID = ft[0].header['GRID_ID']
                fieldID = ft[0].header['FIELD_ID']
                jd = ft[0].header['JD']
        except Exception as e:
            print(e)
        return unitID, camID, gridID, fieldID, jd
    
    def setTempName(self, tpath, fname, tmpName):
        
        try:
            objPath = "%s/%s"%(tpath, fname)
            thdul = fits.open(objPath, mode='update',memmap=False)
            hdl0 = thdul[0].header
            tempPath = hdl0['TEMPNA']
            hdl0['TEMPPH'] = tempPath
            hdl0['TEMPNA'] = tmpName
            thdul[0].header = hdl0
            thdul.close()
        except Exception as e:
            print(e)
    
    def send(self, tpath, objCat, tempCat=""):
        
        objPath = "%s/%s"%(tpath, objCat)
        tempPath = "%s/%s"%(tpath, tempCat)
        
        if len(objCat)>0:
            ccdNoo, fieldNoo, timeStampo, tempPatho, jdo = self.getHeaders(objPath)
        else:
            print("must send objCat")
            return False
            
        if len(tempCat)>0:
            #ccdNot, fieldNot, timeStampt, tempPatht, jdt = self.getHeaders(tempPath)
            summary = "%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n"%(tempCat,ccdNoo, fieldNoo, timeStampo, 
                                                          objCat,ccdNoo, fieldNoo, timeStampo)
            print("\n*************send template")
        else:
            summary = "%s\n%s\n%s\n%s"%(objCat,ccdNoo, fieldNoo, timeStampo)
            print("\n*************send science")
        print("%s"%(summary))
        
        ret = self.sendMsg(summary)
        if ret:
            if len(tempCat)>0:
                trst = self.sendFile(tempPath)
                if not trst:
                    print("send template %s error"%(tempCat))
            trst = self.sendFile(objPath)
            if not trst:
                print("send science %s error"%(objCat))
        else:
            print("send summary error, stop send file")
            return False

        return True

    #JD, GRID_ID, FIELD_ID, UNIT_ID, CAM_ID, TEMPNA
    def getTemplate(self, tpath, sciCat, ssh):
        
        rstFlag = True
        newTempName = ''
        
        twcsFits = 'refcom_astwcs.fit'
        tpath1 = "%s/%s"%(tpath, sciCat)
        ccdNoo, fieldNoo, timeStampo, tempPatho, jdo = self.getHeaders(tpath1)
                
        try:
            ftp = ssh.open_sftp()
            
            srcWcsFits = "%s/%s"%(tempPatho, twcsFits)
            #print("refcom_astwcs.fit=%s"%(srcWcsFits))
            dstWcsFits = "%s/%s"%(tpath, twcsFits)
            os.system("rm -rf %s"%(dstWcsFits))
            ftp.get(srcWcsFits,dstWcsFits)
            
            if os.path.exists(dstWcsFits):
                unitID, camID, gridID, fieldID, jd = self.getHeaders2(dstWcsFits)
                jdStr = str(jd)
                jdStr = jdStr.split('.')
                jdStr = ''.join(jdStr)
                newTempName = "Temp_G%s_%s_%s_%s.Fcat"%(camID,gridID,fieldID,jdStr)
                
                #tcmd = "tcsh -c 'source ~/prog_DifIm/cshrc_difim ; cd %s ; GWSex.sh -i %s -o %s ; ~/prog_DifIm/myprog/bin/wcs2cat.csh %s %s'"%\
                #    (tempPatho, twcsFits, newTempName, twcsFits, newTempName)
                remoteCmd = '~/prog_DifIm/myprog/bin/myenv.csh'
                tcmd = 'cd %s ; %s "GWSex.sh -i %s -o %s" ; %s "wcs2cat.py -w %s %s -f fits_ldac"'% \
                     (tempPatho, remoteCmd, twcsFits, newTempName, remoteCmd, twcsFits, newTempName)
                print(tcmd)
                stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
                for line in iter(stdout.readline, ""):
                    print(line)
                
                srcTemp = "%s/%s"%(tempPatho, newTempName)
                dstTemp = "%s/%s"%(tpath, newTempName)
                os.system("rm -rf %s"%(dstTemp))
                ftp.get(srcTemp,dstTemp)
                ftp.close()
                
                if os.path.exists(dstTemp):
                    thdul = fits.open(dstTemp, mode='update',memmap=False)
                    hdl0 = thdul[0].header
                    hdl0['UNIT_ID'] = unitID
                    hdl0['CAM_ID'] = camID
                    hdl0['GRID_ID'] = gridID
                    hdl0['FIELDID'] = fieldID
                    hdl0['JD'] = jd
                    hdl0['TEMPNA'] = newTempName
                    thdul[0].header = hdl0
                    thdul.close()
                    
                    self.setTempName(tpath, sciCat, newTempName)
                    
                    tstr = "make template success: %s/%s"%(tpath, sciCat)
                    print(tstr)
                else:
                    tstr = "make template failure: %s/%s"%(tpath, sciCat)
                    print(tstr)
                    rstFlag = False
            else:
                print("orig fits file does exist: %s"%(srcWcsFits))
                rstFlag = False
            
        except Exception as e:
            tstr = "get template of %s/%s error: %s"%(tpath, sciCat, str(e))
            print(tstr)
            tstr = traceback.format_exc()
            print(tstr)
            rstFlag = False
            
        return rstFlag, newTempName


    def sendPath(self, tpath, ssh):
        
        os.system("rm -rf %s/Temp*"%(tpath))
        os.system("rm -rf %s/refcom*"%(tpath))
        
        tfiles = os.listdir(tpath)
        tfiles.sort()
        tcats = []
        for tfile in tfiles: 
            if tfile.find("Fcat")>-1 and tfile.find("objt")>-1:
                tcats.append(tfile)
              
        tempFlag = True
        tempCat='' 
        totalImg = len(tcats)
        sendSuccess = 0
        tempFieldNoo=''
        timgIdx = 0
        for tcat in tcats:
            tpath1 = "%s/%s"%(tpath, tcat)
            ccdNoo, fieldNoo, timeStampo, tempPatho, jdo = self.getHeaders(tpath1)
            if len(ccdNoo)==0:
                continue
            if tempFieldNoo!=fieldNoo:
                tempFieldNoo = fieldNoo
                tempFlag, tempCat = self.getTemplate(tpath, tcat, ssh)
                timgIdx = 0
                if tempFlag:
                    self.sendMsg('reset')
                    time.sleep(10)
                else:
                    print("cannot find template, stop.")
                
            if tempFlag:
                print("start send %s"%(tcat))
                if timgIdx == 0:
                    rst = self.send(tpath, tcat, tempCat)
                else:
                    self.setTempName(tpath, tcat, tempCat)
                    rst = self.send(tpath, tcat, "")
                if rst:
                    sendSuccess = sendSuccess+1
                print("field:%s, %dth send done\n"%(tempFieldNoo, timgIdx+1))
            else:
                if timgIdx<5:
                    print("field:%s, no template"%(tempFieldNoo))
            timgIdx = timgIdx+1
            os.system("rm -rf %s"%(tpath1))
            #if timgIdx>10:
            #    break
        return totalImg, sendSuccess

#tar -c *.Fcat | ssh gwaclc@190.168.1.197 'tar -xf - -C /home/gwaclc/work/GWAC_Catalog_2_NetCenter/tmp/181226'
if __name__ == '__main__':
    
    tip='172.28.2.44'
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect(tip, username=sftpUser, password=sftpPass)  
    
    
    tpath = "/home/gwaclc/work/GWAC_Catalog_2_NetCenter/tmp/181214/G004_044"
    gdc = GWACDataClient('10.0.82.111', '12626')
    gdc.sendPath(tpath, ssh)

    ssh.close()