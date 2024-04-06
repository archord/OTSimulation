#!/usr/bin/env python

"""
Usage: python raw2fits.py 1.RAW 2.RAW 3.RAW 4.RAW ....RAW

Give any number of RAW file names in the command line.
If any of the generating *.fits exists, the program will terminate and tell you which one exists.
If there is no corresponding *.fits file exist, the program will run and transform RAW files to FITS in iteration automatically.
"""

# Not in use:
# from intelhex import IntelHex
# ih = IntelHex()
# ih.fromfile(sys.argv[1],format='bin')
import sys,os
import struct
import numpy as np
import astropy.io.fits as pyfits
import os,sys,time,glob
homedir=os.environ["HOME"]

sys.path.append(homedir+"/vvppsoft/vvpython")
import Qfunctions as Q

#from pyraf import iraf
#import pyfits as py


#width = 2147
#height = 1028
#width = 2154
#height = 2052
#width=2048+50+50+10+10
#height=2048+4+20
width=2048
height=2048
#width=1072
#height=1027
def raw2fits(rawname):
    namelist=Q.dec_dataname(rawname)
    for line in namelist:
        rawname=line.strip().split()[0]
        print("raw data:",rawname)
        basename,ext=rawname.split(".")
        fitsname=basename+".fits"
        raw=open(rawname,'r')
        binarr = raw.read(1)
        raw.close()
#       pixtuple = struct.unpack('<'+'h'*width*height,binarr[0:width*height*2])
        pixtuple = struct.unpack('>'+'h'*width*height,binarr[0:width*height*2])
#       pixtuple = struct.unpack('@'+'f'*width*height,binarr[0:width*height*2])
        pixarray = np.array(pixtuple,dtype=np.int16).reshape(height,width)
#       pixarrud = np.flipud(pixarray)

#       hdu = pyfits.PrimaryHDU(pixarrud)
        hdu = pyfits.PrimaryHDU(pixarray)
        hdu.scale('int16','',bzero=32768)
        hdr= hdu.header

        hdulist = pyfits.HDUList([hdu])
#       fitsname = sys.argv[i].replace('.RAW', '.fits')
        if os.path.isfile(fitsname): os.remove(fitsname)

        hdulist.writeto(fitsname)

#       del binarr,pixtuple,pixarray,pixarrud,hdu,hdulist
        del binarr,pixtuple,pixarray,hdu,hdulist

        print(fitsname)
if __name__=='__main__':
    rawname=sys.argv[1]
    raw2fits(rawname)
