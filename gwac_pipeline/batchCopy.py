import numpy as np
import psycopg2
import time
import logging
import os
from astropy.wcs import WCS
from datetime import datetime
import traceback
import paramiko

#nohup python getOTImgsAll.py > /dev/null 2>&1 &
class GWACWCSIndex:
    
    orgImgRoot = '/data/gwac_data/gwac_orig_fits'
    wcsIdxRoot = '/data/gwac_data/gwac_wcs_idx'
    
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
    
    
    def connDb(self):
        
        self.conn = psycopg2.connect(**self.connParam2)
        
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
            self.log.error(" query data error ")
            self.log.error(err)
            
        return np.array(rows)
    
    def queryObs(self, tdata):
            
        tsql = "SELECT img_name FROM fits_file2_his WHERE cam_id=%d AND sky_id=%d " \
            "AND img_name LIKE '%%mon_objt_%d%%' ORDER BY ff_id"%(tdata[2], tdata[1], tdata[0])
        
        return self.getDataFromDB(tsql)

    def copy(self):
        
        root = '/data/gwac_data/gwac_orig_fits'
        desRoot = '/home/xy/work/imgDiffTest2'
        obsSky=[[190121,2578,19],
            [190122,2578,14],
            [190123,2578,14],
            [190124,2578,19],
            [190124,2578,14],
            [190125,2578,19],
            [190125,2578,14],
            [190126,2578,14],
            [190127,2578,14],
            [190128,2578,19]]
        
        sftpUser  =  'xy'
        sftpPass  =  'l'
        pc870 = '10.36.1.211'
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
        ssh.connect(pc870, username=sftpUser, password=sftpPass)
        ftp = ssh.open_sftp()
        for tobs in obsSky:
            timgs = self.queryObs(tobs)
            print("query image %d"%(timgs.shape[0]))
                
            camId = int(tobs[2])
            mountId = int(camId/5)+1
            camId2 = camId%5
            camName = "G%03d_%02d%d"%(mountId, mountId, camId2)
            tpath = "%s/%d/%s"%(root, tobs[0], camName)
            
            destDir = "%s/%d_%s"%(desRoot,tobs[0],camName)
            print(destDir)
            tcmd = "mkdir -p %s;"%(destDir)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                self.log.debug(line)
                
            for img in timgs:
                    
                try:
                    imgPath = "%s/%s"%(tpath, img[0])
                    imgPathfz = "%s/%s.fz"%(tpath, img[0])
                    if os.path.exists(imgPathfz):
                        destPath = "%s/%s.fz"%(destDir,img[0])
                        print(destPath)
                        ftp.put(imgPathfz,destPath)
                    elif os.path.exists(imgPath):
                        destPath = "%s/%s"%(destDir,img[0])
                        print(destPath)
                        ftp.put(imgPathfz,destPath)
                    #break
                #break
                    
                except paramiko.AuthenticationException:
                    print("Authentication Failed!")
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
                except paramiko.SSHException:
                    print("Issues with SSH service!")
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
                except Exception as e:
                    print(str(e))
                    tstr = traceback.format_exc()
                    self.log.error(tstr)
        
        try:
            time.sleep(1)
            ftp.close()
            ssh.close()
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
        
if __name__ == '__main__':
    
    wcsIdx = GWACWCSIndex()
    wcsIdx.copy()
