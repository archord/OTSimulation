# -*- coding: utf-8 -*-
import requests
import time
import os
from requests.auth import HTTPBasicAuth

def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(1,5):
        if i!=1:
            continue
        for j in range(1,6):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips

def getIpList2():
    
    ipPrefix   =  '172.28.100.'
    
    ips = []
    for i in range(1,14):
        if i not in (7,9):
            continue
        ip = "%s%d"%(ipPrefix, i)
        ips.append(ip)
    return ips

def doShutdown():

    idrac_user = "root"
    idrac_password = "calvin"
        
    # ips = getIpList2()
    ips = ['10.36.1.140']
    for idrac_ip in ips:
        
        try:
            print("process %s"%(idrac_ip))

            # iDRAC API URL
            # github开源项目：https://github.com/spyroot/idrac_ctl
            url = f"https://{idrac_ip}/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"

            # API 请求头
            headers = {
                'Content-Type': 'application/json',
            }

            # 请求负载：启动服务器 On, 关闭服务器 GracefulShutdown ForceOff
            payload = {
                "ResetType": "On"
            }

            # 发送POST请求启动服务器
            response = requests.post(url, json=payload, headers=headers, auth=HTTPBasicAuth(idrac_user, idrac_password), verify=False)

            print("服务器启动成功")
            # if response.status_code == 200:
            #     print("服务器启动成功")
            # else:
            #     print(f"服务器启动失败: {response.status_code} - {response.text}")
            
        except Exception as e:
            tstr = "doShutdown %s error: %s"%(idrac_ip, str(e))
            print(tstr)
        
        time.sleep(1)
        #break

if __name__ == '__main__':
    
    doShutdown()    

