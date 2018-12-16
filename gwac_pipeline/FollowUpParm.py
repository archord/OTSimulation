# -*- coding: utf-8 -*-

class FollowUpParm:
    
    def __init__(self):
        
        self.userName = "gwac"
        self.followName = ""
        self.otName = ""
        self.ra = 0.0
        self.dec = 0.0
        self.expTime = ""
        self.frameCount = ""
        self.filter = ""
        self.priority = 20
        self.begineTime = ""
        self.endTime = ""
        self.triggerType = ""
        self.epoch = "2000"
        self.imageType = "LIGHT"
        self.telescope = ""
        self.comment = ""
        
    def getFollowUpString(self):
        
        tstr = ""
        
        return tstr