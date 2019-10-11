# -*- coding: utf-8 -*-
import numpy as np
import os
import psycopg2
import requests
import traceback
from datetime import datetime
            
def uploadObservationPlan(obsId, mode, btime, etime):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/uploadObservationPlan.action"%(serverIP)
        
        values = {'opSn': obsId, 
                  'obsType': mode, 
                  'beginTime': btime, 
                  'endTime': etime}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
      
def updateMountLinked(gid, uid, linked):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/updateMountLinked.action"%(serverIP)
        
        values = {'gid': gid, 
                  'uid': uid, 
                  'linked': linked}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def updateMountState(gid, uid, utc, state, errcode, ra, dec,azi, alt):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/updateMountState.action"%(serverIP)
        
        values = {'gid': gid, 
                  'uid': uid, 
                  'ctime': utc, 
                  'state': state, 
                  'errcode': errcode, 
                  'ra': ra, 
                  'dec': dec, 
                  'azi': azi, 
                  'alt': alt}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)

def updateCameraLinked(gid, uid, cid, linked):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/updateCameraLinked.action"%(serverIP)
        
        values = {'gid': gid, 
                  'uid': uid, 
                  'cid': cid, 
                  'linked': linked}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def uploadCameraStatus(gid, uid, cid, utc, state, errcode, coolget):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/uploadCameraStatus.action"%(serverIP)
        
        values = {'groupId': gid, 
                  'unitId': uid, 
                  'camId': cid, 
                  'utc': utc, 
                  'state': state, 
                  'errcode': errcode, 
                  'coolget': coolget}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def updateCameraCoverLinked(gid, uid, cid, linked):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/updateCameraCoverLinked.action"%(serverIP)
        
        values = {'gid': gid, 
                  'uid': uid, 
                  'cid': cid, 
                  'linked': linked}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
        
def uploadCameraCoverStatus(gid, uid, cid, utc, state, errcode):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/uploadCameraCoverStatus.action"%(serverIP)
        
        values = {'groupId': gid, 
                  'unitId': uid, 
                  'camId': cid, 
                  'utc': utc, 
                  'state': state, 
                  'errcode': errcode}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def updateDomeLinked(gid, linked):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/updateDomeLinked.action"%(serverIP)
        
        values = {'gid': gid, 
                  'linked': linked}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def uploadDomeStatus(gid, utc, state, errcode):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/uploadDomeStatus.action"%(serverIP)
        
        values = {'gid': gid, 
                  'utc': utc, 
                  'state': state, 
                  'errcode': errcode}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def uploadRainfall(gid, utc, value):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/uploadRainfall.action"%(serverIP)
        
        values = {'gid': gid, 
                  'utc': utc, 
                  'value': value}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def uploadObservationPlanRecord(opId, state, ctime):
        
    try:
        #serverIP='172.28.9.14'
        serverIP='127.0.0.1'
        turl = "http://%s:8080/gwebend/uploadObservationPlanRecord.action"%(serverIP)
        
        values = {'opId': opId, 
                  'state': state, 
                  'ctime': ctime}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def testUpload():
    
    #uploadObservationPlan(obsId='2019092743075', mode='1', btime='20190919T180000', etime='20190919T180200')
    #uploadObservationPlanRecord(opId='2019091943075', state='over', ctime='20190920T181234')
    ''''''
    updateMountLinked(gid='001', uid='001', linked='false')
    updateCameraLinked(gid='001', uid='001', cid='001', linked='false')
    updateCameraCoverLinked(gid='001', uid='001', cid='001', linked='false')
    updateDomeLinked(gid='001', linked='false')
    
    ''' 
    updateMountState(gid='001', uid='001', utc='20190921T181234', state=1, errcode=11, ra=63.1, dec=77.2,azi=10.2, alt=1.5)
    uploadCameraStatus(gid='001', uid='001', cid='001', utc='20190922T181234', state=1, errcode=12, coolget=-51.5)
    uploadCameraCoverStatus(gid='001', uid='001', cid='001', utc='20190923T181234', state=1, errcode=13)
    uploadDomeStatus(gid='001', utc='20190924T181234', state=1, errcode=14)
    uploadRainfall(gid='001', utc='20190925T181234', value=128.9)
    '''
if __name__ == "__main__":
    
    testUpload()