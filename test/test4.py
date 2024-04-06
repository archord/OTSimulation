import math

def getGreatCircleDistance(ra1, dec1, ra2, dec2):
    rst = 57.295779513 * math.acos(math.sin(0.017453293 * dec1) * math.sin(0.017453293 * dec2)
            + math.cos(0.017453293 * dec1) * math.cos(0.017453293 * dec2) * math.cos(0.017453293 * (math.fabs(ra1 - ra2))));
    return rst

ra1 = 100.11
dec1 = 59.5
ra2 = 100.381
dec2 = 59.5131

tdist = getGreatCircleDistance(ra1, dec1, ra2, dec2)
tdist = tdist*60
print(tdist)

ra1 = 100.11
dec1 = 59.5
ra2 = 99.9347
dec2 = 59.4614

tdist = getGreatCircleDistance(ra1, dec1, ra2, dec2)
tdist = tdist*60
print(tdist)