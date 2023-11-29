
from gwacFitsRealtimeCollect import GWACQuery
import paramiko
import os

def getCamIpMap():
    
    ipPrefix   =  '172.28.2.'
    
    camIpMap = {}
    for mountIdx in range(1,5):
        for camIdx in range(1,5):
            camName = "G%02d%d"%(mountIdx, camIdx)
            ip = "%s%d%d"%(ipPrefix, mountIdx,camIdx)
            camIpMap[camName]=ip
    return camIpMap

def collectData():

    #查询开始时间
    startTimeUtc = '2023-11-29 10:46:32'
    #查询结束时间
    endTimeUtc = '2023-11-29 10:47:32'
    #存储目录
    rootPath = "/Users/xy/work/python/OTSimulation"

    sftpUser  =  'gwac'
    sftpPass  =  'gwac1234'
    camIPMap = getCamIpMap()
    print(camIPMap)

    gwacQuery = GWACQuery()
    dbrows = gwacQuery.queryFitsListByTime(startTimeUtc, endTimeUtc)

    #将文件参相减进行存储
    datasByCam = {}
    for trow in dbrows:
        camName = "G"+trow[0]
        if camName not in datasByCam:
            datasByCam[camName] = [trow]
        else:
            datasByCam[camName].append(trow)

    imgNum = len(dbrows)
    print("query %d rows"%(imgNum))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )

    for camName in datasByCam:

        #如果不再目标相机列表（camIPMap）中，则直接跳过
        if camName not in camIPMap:
            continue

        trows = datasByCam[camName]
        tnum = len(trows)
        if tnum==0:
            continue

        tip = camIPMap[camName]
        print(camName, tnum, tip)
        ssh.connect(tip, username=sftpUser, password=sftpPass)
        ftp = ssh.open_sftp()

        for i in range(tnum):
            trow = trows[i]
            # camName = "G"+trow[0]
            ffId = trow[1]
            imgName = trow[2]
            imgPath = trow[3]

            dateStr = '20'+imgName[14:20]
            savePath = "%s/%s/%s"%(rootPath, dateStr, camName)
            # print(camName, savePath, tip, ffId, imgName, imgPath)
            print("%s save to %s"%(imgName, savePath))

            if not os.path.exists(savePath):
                os.makedirs(savePath)
            fullPath = "%s/%s"%(savePath, imgName)
            ftp.get(imgPath,fullPath)

            if i>0:
                break
        ftp.close()
    
    
    
if __name__ == '__main__':
    
    collectData()