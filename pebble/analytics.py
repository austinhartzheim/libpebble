#!/usr/bin/env python

from urllib2 import urlopen, Request
from urllib import urlencode
import datetime
import time
import logging
import os
import platform
import uuid

DEBUG = True


####################################################################
####################################################################
class _Analytics(object):
    """ Internal singleton that contains globals and functions for the 
    analytics module """
    
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = _Analytics()
        return cls._instance


    ####################################################################
    def __init__(self):
        """ Initialize the analytics module. 
        
        Here we do one-time setup like forming the client id, checking
        if this is the first time running after an install, etc. 
        """
        
        self.trackingId = 'UA-30638158-7'
        self.endpoint = 'https://www.google-analytics.com/collect'
        # TODO: Generate this
        self.clientId = '35009a79-1a05-49d7-b876-2b884d0f825b'
        
        curSDKVersion = self._getVersion()
        osStr = platform.platform()
        self.userAgent = 'Pebble SDK/%s (%s-python-%s' % (curSDKVersion, 
                            osStr, platform.python_version()) 
        
        
        # Get installation info. If we detect a new install, post an 
        # appropriate event
        homeDir = os.path.expanduser("~")
        settingsDir = os.path.join(homeDir, ".pebble")
        if not os.path.exists(settingsDir):
            os.makedirs(settingsDir)
            
        # Get (and create if necessary) the client id
        try:
            clientId = open(os.path.join(settingsDir, "client_id")).read()
        except:
            clientId = None
        if not clientId:
            clientId = str(uuid.uuid4())
            with open(os.path.join(settingsDir, "client_id"), 'w') as fd:
                fd.write(clientId)

        self.clientId = clientId
            
        # Detect if this is a new install and send an event if so
        try:
            cachedVersion = open(os.path.join(settingsDir, "sdk_version")).read()
        except:
            cachedVersion = None
        if not cachedVersion or cachedVersion != curSDKVersion:
            with open(os.path.join(settingsDir, "sdk_version"), 'w') as fd:
                fd.write(curSDKVersion)
            if cachedVersion is None:
                action = 'firstTime'
            else:
                action = 'upgrade'
            self.postEvent(category='install', action=action, 
                           label=curSDKVersion)

        
        
    ####################################################################
    def _getVersion(self):
        """ Get the SDK version """
        try:
            from VersionGenerated import SDK_VERSION
            return SDK_VERSION
        except:
            return "'Development'"
        
        
    ####################################################################
    def postEvent(self, category, action, label, value=None):
        """ Send an event to the analytics collection server. 
        
        Parameters:
        ----------------------------------------------------------------
        category: The event category
        action: The event action
        label: The event label
        value: The optional event value (integer)
        """
    
        data = {}
        data['v'] = 1
        data['tid'] = self.trackingId
        
        #TODO: generate this from host information
        data['cid'] = self.clientId
        
        # Generate an event
        data['t'] = 'event'
        data['ec'] = category
        data['ea'] = action
        data['el'] = label
        if value:
            data['ev'] = value
            
        # Convert all strings to utf-8
        for key,value in data.items():
            if isinstance(value, basestring):
                data[key] = value.encode('utf-8')
                
        headers = {
                'User-Agent': self.userAgent
                } 
        request = Request(self.endpoint,
                          data=urlencode(data),
                          headers = headers)
        urlopen(request)
        
        # Debugging output?
        logging.debug("[Analytics] header: %s, data: %s" % (headers, data))
        
    
####################################################################
# Our public functions for posting events to analytics
def cmdSuccessEvt(cmdName):
    _Analytics.get().postEvent(category='pebbleCmd', action=cmdName, 
                              label='success')

def cmdFailEvt(cmdName, reason):
    _Analytics.get().postEvent(category='pebbleCmd', action=cmdName, 
               label='fail: %s' % (reason))
    
def cmdMissingPythonDependency(text):
    _Analytics.get().postEvent(category='pythonDependency', action='import', 
               label='missing import: %s' % (text))


####################################################################
if __name__ == '__main__':
    _Analytics.get().postEvent('newCategory', 'newAction', 'newLabel')
    


