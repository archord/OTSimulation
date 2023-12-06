# -*- coding: utf-8 -*-
import sys
import time
import subprocess
from datetime import datetime
import traceback

    
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
    
    #pythonPath = '/home/gwac/software/anaconda3/envs/imgdiff3/bin/python'
    pythonPath = '/data/work/program/image_diff_base/anaconda3/envs/imgdiff3/bin/python'

    #{'name':'diff_remote_daemon','path':'/data/work/program/batch_script', 'parms':'SchedulingSingle start'},
    #{'name':'MonitorShutter','path':'/data/work/program/chbsoft', 'parms':''},
            #{'name':'01gwac_backup_fits4','path':'/data/gwac_data/batch_script', 'parms':''}]
    procList=[{'name':'diff_remote_daemon','path':'/data/work/program/batch_script', 'parms':'SchedulingSingle start'},
            {'name':'diff_remote_daemon','path':'/data/work/program/batch_script', 'parms':'CreateWCSIndex_local start'},
              {'name':'04MachineParameterCollection','path':'/data/work/program/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0021','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0022','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0023','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0024','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0025','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0031','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0032','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0033','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0034','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0035','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0041','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0042','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0043','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0044','path':'/data/gwac_data/batch_script', 'parms':''},
            {'name':'01gwac_backup_fits4_G0045','path':'/data/gwac_data/batch_script', 'parms':''}
	    ]
            
    for proc in procList:
        
        if checkIsDaemonRun(proc['name'], proc['parms']):
            print("process %s %s is running"%(proc['name'], proc['parms']))
        else:
            print("process %s is not running, start..."%(proc['name']))
            tcommand = 'cd %s ; nohup %s %s.py %s > %s.txt &'%(proc['path'], pythonPath, proc['name'], proc['parms'], proc['name'])
            process= subprocess.Popen(tcommand, shell=True, stdout=subprocess.PIPE)
            (stdoutstr,stderrstr) = process.communicate()
            print(stdoutstr)
            print(stderrstr)
        
        time.sleep(1)
