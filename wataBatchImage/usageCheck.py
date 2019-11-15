# -*- coding: utf-8 -*-
import sys
import time
import subprocess
from datetime import datetime
import traceback
import os

def cleanDisk():
    spath1 = r'/data/wata_data/fits_orig'
    dpath1 = r'/data/wata_data/fits_preview'
    

def diskUsePercentage():

    paths = ["root", "data"]
    devs = ["sda2","sda4"]
    uses = [0,0]
                
    try:

        tcmd = "df -T"
        process= subprocess.Popen(tcmd, shell=True, stdout=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        stdoutstr = stdoutstr.decode("utf-8")
        for line in iter(stdout.readline, ""):
            for ii, tdev in enumerate(devs):
                if line.find(tdev)>-1:
                    strs = line.split()
                    if len(strs)==7 and strs[5].find("%")>-1:
                        #tuse = strs[5][:-1]
                        tsize = float(strs[2])
                        tused = float(strs[3])
                        uses[ii]=tused/tsize
                        break

    except Exception as err:
        print(" update disk use error ")
        print(err)
        tstr = traceback.format_exc()
        print(tstr)
    
def checkIsDaemonRun(procName, parms):
    
    #procName='diff_remote_daemon'
    tcmd = 'ps aux | grep %s'%(procName)
    process= subprocess.Popen(tcmd, shell=True, stdout=subprocess.PIPE)
    #output = process.stdout.read()
    #process.stdout.close()
    #process.wait()
    (stdoutstr,stderrstr) = process.communicate()
    stdoutstr = stdoutstr.decode("utf-8")
    
    is2Alive = False
    fullName = "%s.py"%(procName)
    if stdoutstr.find(fullName)>-1: #.decode("utf-8")  .encode('ascii')
        if len(parms)>0:
            if stdoutstr.find(parms)>-1:
                is2Alive = True 
        else:
            is2Alive = True       
        
    return is2Alive
        
if __name__ == '__main__':
    
    diskUsePercentage()