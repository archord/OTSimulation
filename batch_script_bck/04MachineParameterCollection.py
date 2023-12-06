# -*- coding: utf-8 -*-
import os
import paramiko
import time
from datetime import datetime
import hashlib
import requests
from datetime import datetime, timedelta
import time
import psycopg2
import traceback


def updateMachineParameter(ccdname, parmName, parmValue):
    
    connParam2={
        "host": "172.28.8.28",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    
    try:
        
        sql = "update system_status_monitor set %s_used_time=CURRENT_TIMESTAMP, %s_used=%.3f where identity='%s'"%(parmName, parmName, parmValue, ccdname)
        #print(sql)
        conn = psycopg2.connect(**connParam2)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
        
        conn.close()
    except Exception as err:
        print(" update %s set %s=%.3f error "%(ccdname, parmName, parmValue))
        print(err)
        tstr = traceback.format_exc()
        print(tstr)

def sendMsg(msgSession, tmsg):
    
    try:
        sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        tmsg = "%s: %s"%(sendTime, tmsg)
        msgURL = "http://172.28.8.8:8080/gwebend/sendTrigger2WChart.action?chatId=gwac004&triggerMsg="
        turl = "%s%s"%(msgURL,tmsg)
        msgSession.get(turl, timeout=10, verify=False)
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(2,5):
        for j in range(1,6):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips
    
def diskUsePercentage(ssh, msgSession, ip):

    connParam2={
        "host": "172.28.8.28",
        "port": "5432",
        "dbname": "gwac2",
        "user": "gwac",
        "password": "gdb%980"
        }
    paths = ["root","data","data1","data2","data3"]  
    devs = ["centos-root","centos-home","sdb","sdc","sdd"]  
    uses = [0,0,0,0,0]
    
    tcmd = "df -T"
    stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
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
        
    try:
        
        conn = psycopg2.connect(**connParam2)
        for ii, tpath in enumerate(paths):
            ccdName = "0%s"%(ip[-2:])
            print("%s %s use %.1f"%(ccdName, tpath, uses[ii]*100))
        
            sql = "update system_status_monitor set %s_used_time=CURRENT_TIMESTAMP, %s_used=%.3f where identity='%s'"%(tpath, tpath, uses[ii], ccdName)
            #print(sql)
            cur = conn.cursor()
            cur.execute(sql)
            
        conn.commit()
        cur.close()
        conn.close()
    except Exception as err:
        print(" update disk use error ")
        print(err)
        tstr = traceback.format_exc()
        print(tstr)
        
        
def collectAllMachineParm(msgSession, idx):
    
    if idx%6==1:
        tstr = "%d collection data process machine status parameter "%(idx)
        print(tstr)
        sendMsg(msgSession, tstr)
    
    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    ips = getIpList()
            
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
        
    for tip in ips:
        
        try:
            ssh.connect(tip, username=sftpUser, password=sftpPass)
            diskUsePercentage(ssh, msgSession, tip)
        except paramiko.AuthenticationException:
            print("Authentication Failed!")
        except paramiko.SSHException:
            print("Issues with SSH service!")
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
        try:
            time.sleep(1)
            ssh.close()
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        #break

if __name__ == '__main__':
    
    idx = 1
    while True:
        try:
            msgSession = requests.Session()
            collectAllMachineParm(msgSession, idx)
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        finally:
            time.sleep(10*60)
            idx = idx + 1
    
    
