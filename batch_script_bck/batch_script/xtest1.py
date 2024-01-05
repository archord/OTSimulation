def getIpList():

    ipPrefix   =  '172.28.2.'

    ips = []
    for i in range(2,5):
        for j in range(1,6):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips

iplist = getIpList()
print(iplist)
