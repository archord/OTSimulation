import requests
import numpy as np
import os
from datetime import datetime

baseUrl = "http://10.0.10.236:9000/images/gwac_orig_fits"

#http://10.0.10.236:9000/images/gwac_orig_fits/240128/G004_044/G044_Mon_objt_240128T10345447.fit.fz
def downloadFile(turl, savePath, saveName):

    try:
        if not os.path.exists(savePath):
            os.makedirs(savePath)

        startTime = datetime.now()
        tpath = "%s/%s"%(savePath, saveName)
        fullUrl = "%s/%s"%(baseUrl, turl)

        treq = requests.get(fullUrl)
        if treq.status_code==200:
            with open(tpath, 'wb') as f:
                f.write(treq.content)

            endTime = datetime.now()
            remainSeconds =(endTime - startTime).total_seconds()
            if remainSeconds>1:
                print("download %s, use %.2f seconds"%(saveName, remainSeconds))
        else:
            print("error: %s not exist"%(saveName))

    except Exception as err:
        print("error: download %s error"%(saveName))
        # print(err)


def batchDownload(tpath, fname, savePath):

    if not os.path.exists(savePath):
        os.makedirs(savePath)

    fullPath = "%s/%s"%(tpath, fname)
    my_data = np.genfromtxt(fullPath, delimiter=',', dtype=str)

    skyImgList = {}
    for i, trow in enumerate(my_data):
        if trow[0]=="#":
            continue

        imgPath = trow[0] #/data1/G002_021_230927/G021_Mon_objt_230927T17073939.fit
        tStrs0 = imgPath.split("/")
        imgName = tStrs0[3]
        camDateStr = tStrs0[2] #G002_021_230927

        if camDateStr not in skyImgList:
            skyImgList[camDateStr] = [trow]
        else:
            skyImgList[camDateStr].append(trow)
        
    for skyNum, camDateStr in enumerate(skyImgList):
        if skyNum>=10:
            break
        tdata = skyImgList[camDateStr]
        tnumber = len(tdata)
        for i, trow in enumerate(tdata):

            # if i<=20 or i>=23:
            #     continue

            imgPath = trow[0] #/data1/G002_021_230927/G021_Mon_objt_230927T17073939.fit
            imgX = trow[1]
            imgY = trow[2]

            tStrs0 = imgPath.split("/")
            imgName = tStrs0[3]
            camDateStr = tStrs0[2] #G002_021_230927
            tStrs1 = camDateStr.split("_")
            dateStr = tStrs1[2]
            camName = "%s_%s"%(tStrs1[0], tStrs1[1])

            print("start download %d/%d, %s"%(i+1, tnumber, imgName))
            
            saveName = "%s.fz"%(imgName)
            savePath2 = "%s/%s"%(savePath,camDateStr)
            #240128/G004_044/G044_Mon_objt_240128T10345447.fit.fz
            remotePath = "%s/%s/%s"%(dateStr, camName, saveName)
            # print(remotePath)
            downloadFile(remotePath, savePath2, saveName)

if __name__ == '__main__':

    # tpath = "/Users/xy/work/data/lamost/obsSky"
    # fname = "Observed_index_2023_image_list.txt"
    # savePath = "/Users/xy/work/data/lamost/saveImage"

    tpath = "/data/gwac_data/lamostmatch/obsSky"
    fname = "Observed_index_2023_image_list.txt"
    savePath = "/data/gwac_data/lamostmatch/saveImage"

    batchDownload(tpath, fname, savePath)