# -*- coding:utf-8 -*-
import os
from astropy.time import Time
from astropy.io import fits
import traceback
import time
import requests
import paramiko

class GWACDataClient(object):
    def __init__(self, ip, port, tryTimes = 3):
        super(GWACDataClient, self).__init__()
        self.ip = ip
        self.port = str(port)
        self.tryTimes = tryTimes
        self.sendUrl = "http://%s:%s/fs/uploadCatalogs.action"%(ip,port)
        print(self.sendUrl)

    def reportError(self, msg):
        print(str(msg))

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
    
    def send(self, tpath, objCat, tempCat, isFirst=True):
        
        objPath = "%s/%s"%(tpath, objCat)
        tempPath = "%s/%s"%(tpath, tempCat)
        
        if len(objCat)>0:
            ccdNoo, fieldNoo, timeStampo, tempPatho, jdo = self.getHeaders(objPath)
            timeStampo = timeStampo[:timeStampo.index('.')]
        else:
            print("must send objCat")
            return False

        if isFirst:
            #files = {'obsCat': (objCat, open(objPath,'rb'), 'text/x-spam')}
            files = {'obsCat': (objCat, open(objPath,'rb'), 'application/octet-stream'), 
                     'tmpCat': (tempCat, open(tempPath,'rb'), 'application/octet-stream')}
            values = {'obsCcdName': ccdNoo, 'obsFieldName': fieldNoo, 'obsDateTime': timeStampo,
                      'tmpCcdName': ccdNoo, 'tmpFieldName': fieldNoo, 'tmpDateTime': timeStampo}
            #print(values)
            #print(files)
            r = requests.post(self.sendUrl, files=files, data=values)
            print(r.text)
        else:
            files = {'obsCat': (objCat, open(objPath,'rb'), 'application/octet-stream')}
            values = {'obsCcdName': ccdNoo, 'obsFieldName': fieldNoo, 'obsDateTime': timeStampo,
                      'tmpCcdName': ccdNoo, 'tmpFieldName': fieldNoo, 'tmpDateTime': timeStampo,
                      'tmpCatFileName':tempCat}
            #print(values)
            #print(files)
            r = requests.post(self.sendUrl, files=files, data=values)
            print(r.text)
        
        return True

    def sendTest(self,tpath):
        
        objCat = 'G033_mon_objt_190116T10265300.Fcat'
        tempCat = 'Temp_G033_G0013_35100085_245845293465.Fcat'
        self.send(tpath, objCat, tempCat, True)

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
                srcTemp = "%s/%s"%(tempPatho, newTempName)
                dstTemp = "%s/%s"%(tpath, newTempName)
                
                if not os.path.exists(dstTemp):
                    #tcmd = "tcsh -c 'source ~/prog_DifIm/cshrc_difim ; cd %s ; GWSex.sh -i %s -o %s ; ~/prog_DifIm/myprog/bin/wcs2cat.csh %s %s'"%\
                    #    (tempPatho, twcsFits, newTempName, twcsFits, newTempName)
                    remoteCmd = '~/prog_DifIm/myprog/bin/myenv.csh'
                    tcmd = 'cd %s ; %s "GWSex.sh -i %s -o %s" ; %s "wcs2cat.py -w %s %s -f fits_ldac"'% \
                         (tempPatho, remoteCmd, twcsFits, newTempName, remoteCmd, twcsFits, newTempName)
                    print(tcmd)
                    stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
                    for line in iter(stdout.readline, ""):
                        print(line)
                    
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
            tstr = "get template of error: %s"%( str(e))
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
        
        print("total %d files"%(len(tcats)))
        tempFlag = True
        tempCat='' 
        totalImg = len(tcats)
        sendSuccess = 0
        tempFieldPatho=''
        timgIdx = 0
        for tcat in tcats:
            tpath1 = "%s/%s"%(tpath, tcat)
            ccdNoo, fieldNoo, timeStampo, tempPatho, jdo = self.getHeaders(tpath1)
            jdStr = str(jdo)
            if len(jdStr)<=len('2458468.0'):
                continue
            if len(ccdNoo)==0:
                continue
            if tempFieldPatho!=tempPatho:
                tempFieldPatho = tempPatho
                tempFlag, tempCat = self.getTemplate(tpath, tcat, ssh)
                timgIdx = 0
                
            if tempFlag:
                print("start send %s"%(tcat))
                if timgIdx == 0:
                    rst = self.send(tpath, tcat, tempCat, True)
                else:
                    self.setTempName(tpath, tcat, tempCat)
                    rst = self.send(tpath, tcat, tempCat, False)
                if rst:
                    sendSuccess = sendSuccess+1
                print("field:%s, %dth send done\n"%(fieldNoo, timgIdx+1))
            else:
                if timgIdx<5:
                    print("field:%s, no template"%(fieldNoo))
            timgIdx = timgIdx+1
            os.system("rm -rf %s"%(tpath1))
            #if timgIdx>10:
            #    break
        return totalImg, sendSuccess

#tar -c *.Fcat | ssh gwaclc@190.168.1.197 'tar -xf - -C /home/gwaclc/work/GWAC_Catalog_2_NetCenter/tmp/181226'
if __name__ == '__main__':
    
    tip='172.28.2.33'
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect(tip, username=sftpUser, password=sftpPass)  
    
    
    tpath = "/home/gwaclc/work/GWAC_Catalog_2_NetCenter2/tmp/190116/G003_033"
    gdc = GWACDataClient('10.0.82.111', '8077')
    #gdc = GWACDataClient('10.36.1.77', '8080')
    #gdc.sendPath(tpath, ssh)
    gdc.sendTest(tpath)

    ssh.close()

