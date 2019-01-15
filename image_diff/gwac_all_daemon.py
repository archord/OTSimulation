# -*- coding: utf-8 -*-
import sys
import time
import subprocess
from datetime import datetime
import traceback

    
def checkIsDaemonRun(procName):
    
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
        is2Alive = True       
        
    return is2Alive
        
if __name__ == '__main__':
    
    pythonPath = '/home/gwac/software/anaconda3/envs/imgdiff3/bin/python'
    
    procList=[{'name':'diff_remote_daemon','path':'/data/work/program/batch_script', 'parms':'status'},
              {'name':'04MachineParameterCollection','path':'/data/work/program/batch_script', 'parms':''},
            {'name':'MonitorShutter','path':'/data/work/program/chbsoft', 'parms':''},
            {'name':'01gwac_backup_fits2','path':'/data/gwac_data/batch_script', 'parms':''}]
            
    for proc in procList:
        
        if checkIsDaemonRun(proc['name']):
            print("process %s is running"%(proc['name']))
        else:
            print("process %s is not running, start..."%(proc['name']))
            tcommand = 'cd %s ; nohup %s %s.py %s > %s.txt &'%(proc['path'], pythonPath, proc['name'], proc['parms'], proc['name'])
            process= subprocess.Popen(tcommand, shell=True, stdout=subprocess.PIPE)
            (stdoutstr,stderrstr) = process.communicate()
            print(stdoutstr)
            print(stderrstr)
        
        time.sleep(1)