#!/usr/bin/env python
import os,sys,glob,time
global softwaredir
try:
        softwaredir=os.environ["GWAC_DIR"]
except:
        print "please define GWAC_DIR: the directory of all software and config files"
        sys.exit()
import math
import math
#from scipy import array, arange, size, zeros, mod, floor, sin, cos, arccos, tan, sqrt
from pyraf import iraf
iraf.imcoords
#iraf.pygft(_doprint=0)
#iraf.gftred(_doprint=0)
import Qfunctions as Q
#import gwac_cali 
#import x3_cali 
def jfovcen(ra0,dec0,cali):
        f=open(cali,'r')
        ftmp=f.readline()
        f.close()
        line1=ftmp.strip().split()
        A=line1[0];Z=line1[1];xrotation=line1[2]
        aa="fromaz "+A +" "+Z+" "+str(ra0)+" "+str(dec0)+" "+xrotation+" jfovcen.tmp"
	
        aa_out=os.popen(aa).readlines()
	f=open("jfovcen.tmp","r")
	ftmp=f.readline()
	f.close()
	line1=ftmp.strip().split()
	ra1=float(line1[0]); dec1=float(line1[1])
	if ra1<0: ra1=ra1+360.0
	print "orignal pointing and accurate center of JFOV:",ra0,dec0,ra1,dec1
#        print aa_out
        return ra1,dec1
def lot2(input):
	dir=os.getcwd()
	line1=dir.strip().split("/")
	print line1
	ndir=len(line1)
	log=""
	for i in range(ndir-1):
		if i==ndir-2:	log=log+line1[i+1]
		else:	log=log+line1[i+1]+"_"
	log=log+".log"
	print "log=",log
	flog=open(log,"w")
	fitsname=input[1]
	if len(input)>2: op2="1"
	else: op2="0"
	os.system("cp -f "+softwaredir+"/config.txt .")
	os.system("cp -f "+softwaredir+"/default.* .")
	os.system("cp -f "+softwaredir+"/fort.93 .")
	dtor=3.1415926/180.0
	namelist=Q.dec_dataname(fitsname)
#	os.system("rm -f *ty2*.cat")
  	for line in namelist:
#-----------------------------------------------
	    fail="n"
	    fitsname=line.strip().split()[0]
     	    basename,ext=fitsname.strip().split(".")
    	    print "fitsname=",fitsname
	    ccdtype=Q.getkeyword(fitsname,"CCDTYPE")
	    if ccdtype!="OBJECT": continue
            telescope=Q.getkeyword(fitsname,"TERMTYPE")
            camera=Q.getkeyword(fitsname,"CAM_ID")
	    telescope=telescope+camera
            database,xformat,yformat,scale,pt,x1s,x2s,y1s,y2s,x1p,x2p,y1p,y2p,\
            	  epsi,angle_lowl,angle_upl=Q.deconfig(telescope)
            print telescope,camera
	   
            print "This is a program for astrometric calibrations"
#            os.system("cp ~/gwac_astrometry/software/default.* .")
	    
            sra=Q.getkeyword(fitsname,"RA")
            sdec=Q.getkeyword(fitsname,"DEC")
	    if len(sra.split(":"))==1:
		ra=float(sra)
	    else:
		ra=float(Q.hms2dec(sra))*15.0
            if len(sdec.split(":"))==1:
                dec=float(sdec)
            else:
                dec=float(Q.hms2dec(sdec))
	    print sra,sdec,ra,dec
	    jfovcali="n"
            if telescope[0:4]=="JFoV":
                maglim1=1.0;  maglim2=9.0
                cali=telescope+".cali"
		print "cali=",cali,softwaredir+"/"+cali
	
                if os.path.isfile(softwaredir+"/"+cali):
			os.system("cp "+softwaredir+"/"+cali+" .")
                        print "ther is a position calibration for this camera"
	    		jfovcali="y"
			ra0,dec0=jfovcen(ra,dec,cali)
			ra=ra0;dec=dec0
            if telescope[0:4]=="FFoV":
                 maglim1=5.0;  maglim2=9.0
	    lng,lat=Q.calgalactic(ra,dec)
            fcen=open("cen.xy","w")
            xc=float(xformat)/2.0
            yc=float(yformat)/2.0
            fcen.write(str(xc)+" "+str(yc)+"\n")
            fcen.write("1.0 1.0 \n")
            fcen.write(str(xformat)+" 1\n")
            fcen.write(str(xformat)+" "+str(yformat)+"\n")
            fcen.write("1.0 "+str(yformat)+"\n")
            fcen.write(str(x1p)+" "+str(y1p)+"\n")
            fcen.write(str(x2p)+" "+str(y1p)+"\n")
            fcen.write(str(x2p)+" "+str(y2p)+"\n")
            fcen.write(str(x1p)+" "+str(y2p)+"\n")
            fcen.close()
            fov=(float(x2s)-float(x1s))*float(scale)*1.414/2.0/3600.0
	    ira=int(round(ra*math.cos(dec*dtor))/2);idec=int(round(dec)/2)
	    if idec>=0: 
            	ty2cat= str(ira)+"+"+str(idec)+"_"+telescope[0:4]+"_tyc2.cat"
            	ty2bcat=str(ira)+"+"+str(idec)+"_"+telescope[0:4]+"_tyc2b.cat"
	    else:
		ty2cat= str(ira)+"-"+str(-idec)+"_"+telescope[0:4]+"_tyc2.cat"
                ty2bcat=str(ira)+"-"+str(-idec)+"_"+telescope[0:4]+"_tyc2b.cat"
            if telescope=="xl30cm" and not os.path.isfile("cencc.dat"):
                firstfits=namelist[0].strip().split()[0]
                print "first fits images : ",firstfits
                rac=15.0*Q.hms2dec(Q.getkeyword(firstfits,"OBJCTRA"))
                decc=Q.hms2dec(Q.getkeyword(firstfits,"OBJCTDEC"))
                print "rac decc =",rac,decc
                fcencc=open("cencc.dat","w")
                fcencc.write("%12.6f %12.6f \n" %(rac,decc))
                fcencc.close()

#       radius=radius/2.0
            if telescope[0:4]=="JFoV"  : 
			if jfovcali=="n": 
				radius=18.0*3600.0
			if jfovcali=="y": radius=8.0*3600.0
            if telescope[0:4]=="FFoV"  : radius=8.0*3600.0
            print "radius=",radius
            print ty2cat,ra,dec,radius
	    if idec>=0: 
	    	allangle=str(ira)+"+"+str(idec)+"_"+telescope[0:4]+".aag"
	    	refcat=str(ira)+"+"+str(idec)+"_"+telescope[0:4]+".ref"
	    else: 
		allangle=str(ira)+"-"+str(-idec)+"_"+telescope[0:4]+".aag"
            	refcat=str(ira)+"-"+str(-idec)+"_"+telescope[0:4]+".ref"
	    if not os.path.isfile(ty2cat) or  not os.path.isfile(ty2bcat): 
		if abs(lat)<25: maglim2=8.0 
            	Q.makedsscat1(ty2cat,ra,dec,radius,maglim1,maglim2,600)
		if Q.filelength(ty2cat)<200:
			Q.maketyc2cat(ty2cat,ra,dec,radius,maglim1,maglim2,600)
            	Q.cattrim(ty2cat,ty2bcat,maglim1,maglim2)
	     
            	if telescope[0:4]=="FFoV" : num=100
            	if telescope[0:4]=="JFoV" : 
			if jfovcali=="n": num=400
			else: num=100
#            	aa="triangle1 "+telescope+" "+ty2bcat+" "+str(num)
            	aa="triangle1 FFoV "+ty2bcat+" "+str(num)
            	print aa
            	aa_out=os.popen(aa).readlines()
            	aa="sort triangleall.dat >aangle.dat"
            	os.system(aa)
		os.system("cp aangle.dat "+allangle)
		os.system("cp refcat.dat "+refcat)
	    else:
		os.system("cp "+allangle+" aangle.dat")
		os.system("cp "+refcat+" refcat.dat")
#-----------------------------------------------
	   
	    if not os.path.isfile(basename+".sexb"):
	      subfits1="sub1.fits"
	      subfits2="sub2.fits"
	      if os.path.isfile(subfits1): os.remove(subfits1)
	      if os.path.isfile(subfits2): os.remove(subfits2)
	      iraf.imcopy(fitsname+"["+str(x1s)+":"+str(x2s)+","+str(y1s)+":"+str(y2s)+"]",subfits1)
	      iraf.imcopy(fitsname+"["+str(x1p)+":"+str(x2p)+","+str(y1p)+":"+str(y2p)+"]",subfits2)
	      if os.path.isfile("test.cat"): os.remove("test.cat")

	      for i in range(6):
			sigma1=50.0/(2.0**float(i))
			sigma2=20.0/(2.0**float(i))
                	print i,sigma1,sigma2
                	if telescope[0:4]=="JFoV"  :
                   		os.system("sex  "+subfits1+" -DETECT_THRESH "+str(sigma1)+"  -DETECT_MINAREA 4 -FILTER N -PHOT_APERTURES 10 -SATUR_LEVEL 70000.0")
		   		os.system("read3 "+basename+".sexb1")
			        nstar=Q.filelength(basename+".sexb1")
                                if i==0:
                                        nstar0=nstar
                                        if nstar<50:
							 print "nstar0=",nstar0
							 fail="y" 
						  	 break
                                if nstar>200: break           
			elif telescope[0:4]=="FFoV"  :
			        print "ok"
                                os.system("sex  "+subfits1+" -DETECT_THRESH "+str(sigma2)+"  -DETECT_MINAREA 4 -FILTER N -PHOT_APERTURES 8 -SATUR_LEVEL 60000.0")
                                os.system("read3 "+basename+".sexb1")
			        nstar=Q.filelength(basename+".sexb1")
			        if i==0: 
					nstar0=nstar
                               		if nstar<20: 
							 print "nstar0=",nstar0
							 fail="y" 
							 break
			        if nstar>200: break
	      print "ok1" 
	      if  fail=="y": continue
	      for i in range(6):
		sigma1=100.0/(2.0**float(i))	
		sigma2=50.0/(2.0**float(i))	
		print i,sigma1,sigma2
	    	if telescope[0:4]=="JFoV"  :
			os.system("sex  "+subfits2+" -DETECT_THRESH "+str(sigma1)+"  -DETECT_MINAREA 4 -FILTER N -PHOT_APERTURES 5 -SATUR_LEVEL 60000.0")
			print "sex  "+fitsname+" -DETECT_THRESH "+str(sigma1)+"  -DETECT_MINAREA 4 -FILTER N -PHOT_APERTURES 8 -SATUR_LEVEL 60000.0"
		elif telescope[0:4]=="FFoV" :
                        os.system("sex  "+subfits2+" -DETECT_THRESH "+str(sigma2)+" -DETECT_MINAREA 4 -FILTER N -PHOT_APERTURES 6 -SATUR_LEVEL 60000.0")
			print "sex  "+fitsname+" -DETECT_THRESH "+str(sigma2)+" -DETECT_MINAREA 4 -FILTER N -PHOT_APERTURES 8 -SATUR_LEVEL 60000.0"
#	    	if telescope!="FFoV"  telescope!="FFoV":
		else: 
	        	os.system("sex  "+fitsname+"  -DETECT_THRESH 10 -PHOT_APERTURES 4 -SATUR_LEVEL 60000.0 \
			-SEEING_FWHM  3 ")
	
	    	os.system("read3 "+basename+".sexb")
	    	if Q.filelength(basename+".sexb") <10: break
	    	if Q.filelength(basename+".sexb") >2000: break

	      Q.xyaddzero(basename+".sexb1",basename+".sexb1",x1s,y1s)	
	      Q.xyaddzero(basename+".sexb",basename+".sexb",x1p,y1p)	
#     	    Q.sourcetrim(basename+".sexb1",basename+".xy" ,x1s, x2s, y1s, y2s)
#     	    Q.sourcetrim(basename+".sexb",basename+".xy" ,x1s, x2s, y1s, y2s)
	    if not os.path.isfile(basename+".sexb1"):
			fail="y"
			nstar=0
	    else:
		nstar0=Q.filelength(basename+".sexb1")
		if nstar0<20: fail="y"
	    if fail=="y":
		print "It is fail to process the image: few star in the image"
		flog.write(fitsname+" fail due to the few stars in the image.\n")
	        flog.write("%s %5.5d fail due to the few stars in the image \n" %(fitsname,nstar0)) 
		continue 
	    aa="xyfileter "+basename+".xy "+basename+".xy "+str(x1s)+" "+str(x2s)+\
                " "+str(y1s)+" "+str(y2s )
           # os.system(aa) 
	    Q.filetrim(basename+".sexb1",basename+".xy",100)
		
            if os.path.isfile(basename+".xycc"): os.remove(basename+".xycc")
	
	    aa="tmatch1 "+basename+".xy "+basename+".xycc "+str(scale)+" "+str(angle_lowl)+" "+str(angle_upl)+" "+str(epsi)+" "+str(pt*3.0)
	    if op2=="0":
		if abs(lat)<25: aa_out=os.popen(aa+" 10").readlines()
		aa_out=os.popen(aa+" 20").readlines()
	    	print aa+" 20"
	    if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc") <5 :
            	if op2=="0": 
			if abs(lat)<25: aa_out=os.popen(aa+" 15").readlines()
			aa_out=os.popen(aa+" 30").readlines()
			print aa+" 30"
            if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc")<5 :
                if op2=="0": 
			aa_out=os.popen(aa+" 50").readlines()
                	print aa+" 50"
	    if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc")<5:
       		aa="op2 "+basename+".xy "+basename+".xycc "+database+" "\
                        +str(scale)+" "+str(angle_lowl)+" "+str(angle_upl)+" "+str(epsi)+" "+str(pt*1.0)
        	print aa+" 10"
        	os.system(aa+" 10")
		if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc") <5:
        		os.system(aa+" 15")
		if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc") <5:
             		os.system(aa+" 20")
        		print aa+" 20"
             		if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc") <5:
                  		os.system(aa+" 30")
        			print aa+" 30"
                  		if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc") <5:
                        		os.system(aa+" 40")                        
        				print aa+" 40"
	
            if not os.path.isfile(basename+".xycc") or Q.filelength(basename+".xycc") <5:
		continue
            if os.path.isfile(basename+".xycc") and Q.filelength(basename+".xycc") >=5:
	      if Q.filelength(basename+".xycc") >20:
              	if os.path.isfile(basename+".cc"): os.remove(basename+".cc")
              	iraf.ccmap(basename+".xycc",basename+".cc",solutio="first",\
                         images="",\
                         xcolumn=1, ycolumn=2, lngcolu=3, latcolu=4,\
                         xmin=x1s, ymin=y1s, xmax=x2s, ymax=y2s,lngunit="degrees",\
			 insystem="J2000.0", refpoint="coords",\
			 fitgeometry="general",function="legendre",\
                         xxorder=3, xyorder=3, xxterms="half",yxorder=3,yyorder=3,\
                         yxterms="half",maxiter=3,reject=2.0,\
                         latunit="degrees",inter="no", verbose="yes", update="yes")
              if Q.filelength(basename+".xycc") <=20:
              	if os.path.isfile(basename+".cc"): os.remove(basename+".cc")
              	iraf.ccmap(basename+".xycc",basename+".cc",solutio="first",\
                         images="",\
                         xcolumn=1, ycolumn=2, lngcolu=3, latcolu=4,\
                         xmin=x1s, ymin=y1s, xmax=x2s, ymax=y2s,lngunit="degrees",\
                         fitgeometry="general",function="legendre",\
			 insystem="J2000.0", refpoint="coords",\
                         xxorder=2, xyorder=2, xxterms="none",yxorder=2,yyorder=2,\
                         yxterms="none",maxiter=3,reject=2.0,\
                         latunit="degrees",inter="no", verbose="yes", update="yes")
              if os.path.isfile(basename+".cencc"): os.remove(basename+".cencc")
	      iraf.cctran(input="cen.xy",output=basename+".cencc",database=basename+".cc",\
                        solutions="first",geometry="geometric",forward="yes",\
			xcolumn=1,ycolumn=2,\
			lngunit="degrees", latunit="degrees",\
                        lngformat="%12.6f",latformat="%12.6f")
#	      os.system("getcat "+ basename+".cencc "+basename+".catcc 6.8")
#--------------redo ccmap to project at the center of fov
	      xirms=Q.readacc(basename+".cc","xirms")
	      etarms=Q.readacc(basename+".cc","etarms")
	      if telescope[0:4]=="JFoV": 
	      	if xirms>30 or etarms>30: continue
	      if telescope[0:4]=="FFoV":
                if xirms>80 or etarms>80: continue
              fcencc=open(basename+".cencc",'r')
              fcencctmp=fcencc.readline().strip().split()
              ra1=float(fcencctmp[0]); dec1=float(fcencctmp[1])
              fcencc.close()
              ira1=int(round(ra1*math.cos(dec1*dtor))/2); idec1=int(round(dec1)/2)
              print "new cencc:",ra1,dec1
	      lng,lat=Q.calgalactic(ra1,dec1)
	      print "galactic coords:", lng,lat
              if os.path.isfile(basename+".cc"): os.remove(basename+".cc")
              if Q.filelength(basename+".xycc") >20:
                if os.path.isfile(basename+".cc"): os.remove(basename+".cc")
                iraf.ccmap(basename+".xycc",basename+".cc",solutio="first",\
                         images="",\
                         xcolumn=1, ycolumn=2, lngcolu=3, latcolu=4,\
                         xmin=x1s, ymin=y1s, xmax=x2s, ymax=y2s,lngunit="degrees",\
                         fitgeometry="general",function="legendre",\
			 insystem="J2000.0", refpoint="user",lngref=ra1,latref=dec1,\
                         xxorder=3, xyorder=3, xxterms="half",yxorder=3,yyorder=3,\
                         yxterms="half",maxiter=2,\
                         latunit="degrees",inter="no", verbose="yes", update="yes")
              if Q.filelength(basename+".xycc") <=20:
                if os.path.isfile(basename+".cc"): os.remove(basename+".cc")
                iraf.ccmap(basename+".xycc",basename+".cc",solutio="first",\
                         images="",\
                         xcolumn=1, ycolumn=2, lngcolu=3, latcolu=4,\
                         xmin=x1s, ymin=y1s, xmax=x2s, ymax=y2s,lngunit="degrees",\
                         fitgeometry="general",function="legendre",\
			 insystem="J2000.0", refpoint="user",lngref=ra1,latref=dec1,\
                         xxorder=2, xyorder=2, xxterms="none",yxorder=2,yyorder=2,\
                         yxterms="none",maxiter=2,\
                         latunit="degrees",inter="no", verbose="yes", update="yes")
#-------------------------------------
              if telescope[0:4]=="JFoV":
                maglim1=8; maglim2=11
                radius1=9.9*3600.0
                if idec1>=0:

                        JFoV_cat=str(ira1)+"+"+str(idec1)+"_JFoV_tyc2c.cat"
                else:
                        JFoV_cat=str(ira1)+"-"+str(-idec1)+"_JFoV_tyc2c.cat"
                if not os.path.isfile(JFoV_cat):
	                lng,lat=Q.calgalactic(ra1,dec1)
        	        if abs(lat)<25: maglim2=10.0
                        Q.makedsscat1(JFoV_cat,ra1,dec1,radius1,maglim1,maglim2,2000)
			if Q.filelength(JFoV_cat)<500:
		               Q.maketyc2cat(JFoV_cat,ra1,dec1,radius1,maglim1,maglim2,2000)
#                        Q.cattrim(JFoV_cat,JFoV_cat,maglim1,maglim2)
                os.system("cp "+JFoV_cat+" "+basename+".catcc")
              else:
                print "FFoV:"
                maglim1=6; maglim2=11
                radius1=19.0*3600.0
                if idec1>=0:
                        FFoV_cat=str(ira1)+"+"+str(idec1)+"_FFoV_tyc2c.cat"
                else:
                        FFoV_cat=str(ira1)+"-"+str(-idec1)+"_FFoV_tyc2c.cat"
                if not os.path.isfile(FFoV_cat):
                       	Q.maketyc2cat(FFoV_cat,ra1,dec1,radius1,maglim1,maglim2,2000)
                        if Q.filelength(FFoV_cat)<500:
				maglim1=6.0;maglim2=10.0
				Q.makedsscat1(FFoV_cat,ra1,dec1,radius1,maglim1,maglim2,1000)
                        Q.cattrim(FFoV_cat,FFoV_cat,maglim1,maglim2)
                os.system("cp "+FFoV_cat+" "+basename+".catcc")
#              Q.filetrim(dsscat,basename+".catcc",800)
#--------------first match with stars less than 100----------------------------
#	      os.system("cp "+basename+".catcc "+basename+".catcc1")
	      Q.filetrim(basename+".catcc",basename+".catcc1",600)
              if os.path.isfile(basename+".catxy1"): os.remove(basename+".catxy1")
              iraf.cctran(input=basename+".catcc1",output=basename+".catxy1",database=basename+".cc",\
                        solutions="first",geometry="geometric",forward="no",\
			xcolumn=1,ycolumn=2,\
			lngunit="degrees", latunit="degrees",\
                        lngformat="%12.6f",latformat="%12.6f")
#	      Q.sortfile(basename+".catxy",3,0)
#	      Q.sortfilie(basename+".catcc",3,0)
	      print "x1p,x2p,y1p,y2p",x1p,x2p,y1p,y2p
	      os.system("cp "+basename+".catxy tmp.catxy")
	      Q.sourcestrim(basename+".catxy1",basename+".catcc1",x1p,x2p,y1p,y2p)
	      Q.sourcetrim(basename+".sexb",basename+".bsxy",x1p,x2p,y1p,y2p)
	      Q.filetrim(basename+".bsxy", basename+".bsxy",600)
              aa="xyfileter "+basename+".bsxy "+basename+".bsxy1 "+str(x1p)+" "+str(x2p)+\
                " "+str(y1p)+" "+str(y2p )
	      os.system(aa)
#	
#	      Q.filetrim(basename+".sexb",basename+".bsxy",1200)
# last term in aa is cross-error radius, change to 10"
	      error1=Q.readacc(basename+".cc","xirms")
	      error2=Q.readacc(basename+".cc","etarms")
	      error=((error1*2.0+error2**2.0)**0.5)/scale
	      if telescope[0:4]=="FFoV":  error=30
	      if telescope[0:4]=="JFoV":  error=30
#	      if telescope[0:4]=="JFoV":  error=error*5.0
	      aa="crossxy "+basename+".catxy1 "+basename+".bsxy1 "\
			+basename+".catcc1 "+basename+".axycc "+str(error)
	      print aa
	      os.system(aa)
	      naxycc=Q.filelength(basename+".axycc")
	      print "number of axycc:", naxycc
#	      if naxycc>500: Q.filetrim(basename+".axycc",basename+".axycc",500)
              aa="accfileter "+basename+".axycc "+basename+".axycc1 "+str(x1p)+" "+str(x2p)+\
                 " "+str(y1p)+" "+str(y2p)
              os.system(aa)
	      Q.ccmapfit(basename+".axycc1",basename+".acc1",x1p,x2p,y1p,y2p,ra1,dec1)
#---------------second fitting with stars around 1000------------------------
              os.system("cp "+basename+".catcc "+basename+".catcc2")
              if os.path.isfile(basename+".catxy"): os.remove(basename+".catxy")
              iraf.cctran(input=basename+".catcc2",output=basename+".catxy",database=basename+".acc1",\
                        solutions="first",geometry="geometric",forward="no",\
                        xcolumn=1,ycolumn=2,\
                        lngunit="degrees", latunit="degrees",\
                        lngformat="%12.6f",latformat="%12.6f")
#              Q.sourcestrim(basename+".catxy",basename+".catcc2",x1p,x2p,y1p,y2p)
              Q.sourcetrim(basename+".sexb",basename+".bsxy",x1p,x2p,y1p,y2p)
              aa="xyfileter "+basename+".bsxy "+basename+".bsxy "+str(x1p)+" "+str(x2p)+\
                " "+str(y1p)+" "+str(y2p )
	      os.system(aa)
              error1=Q.readacc(basename+".acc1","xirms")
              error2=Q.readacc(basename+".acc1","etarms")
              error=((error1*2.0+error2**2.0)**0.5)/scale
	      if abs(lat)<25: 
              	if telescope[0:4]=="FFoV":  error=5.0
              	if telescope[0:4]=="JFoV":  error=5.0
              else:
                if telescope[0:4]=="FFoV":  error=5.0
                if telescope[0:4]=="JFoV":  error=5.0
              aa="crossxy "+basename+".catxy "+basename+".bsxy "\
                        +basename+".catcc2 "+basename+".axycc "+str(error)
	      print aa
	      os.system(aa)
	      aa="accfileter "+basename+".axycc "+basename+".axycc "+str(x1p)+" "+str(x2p)+\
		 " "+str(y1p)+" "+str(y2p)
	      os.system(aa)
	      Q.ccmapfit(basename+".axycc",basename+".acc",x1p,x2p,y1p,y2p,ra1,dec1)
	      iraf.cctran(input="cen.xy",output=basename+".cencc1",database=basename+".acc",\
                   solutions="first",geometry="geometric",forward="yes",\
                   xcolumn=1,ycolumn=2,\
                   lngunit="degrees", latunit="degrees",\
                   lngformat="%12.6f",latformat="%12.6f")

	      xirms=Q.readacc(basename+".acc","xirms")
              etarms=Q.readacc(basename+".acc","etarms")
	      flog.write("%s %5.5d %6.2f %6.2f \n" %(fitsname,nstar0,xirms,etarms)) 
        flog.close()
                   
if __name__=='__main__':
       fitsname=sys.argv[1]
       lot2(sys.argv)
#       sys.exit()
