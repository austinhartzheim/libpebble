#!/usr/bin/env python


from urllib2 import urlopen, Request
from urllib import urlencode
import datetime
import time
import logging
import os
import platform
import uuid
import pprint
import subprocess

DEBUG = True

####################################################################
def _runningInVM():
    """ Return true if we are running in a VM """

    inVM = False    
    try:
        drvName = "/proc/scsi/scsi"
        if os.path.exists(drvName):
            contents = open(drvName).read()
            if "VBOX" in contents or "VMware" in contents:
                return True
    except:
        pass
        
    return False


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
        
        curSDKVersion = self._getSDKVersion()
        self.osStr = platform.platform()
        if _runningInVM():
            self.osStr += " (VM)"
        self.userAgent = 'Pebble SDK/%s (%s-python-%s)' % (curSDKVersion, 
                            self.osStr, platform.python_version()) 
        
        
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
            
        # Should we track analytics?
        sdkPath = os.path.normpath(os.path.join(os.path.dirname(__file__), 
                                                '..', '..'))
        dntFile = os.path.join(sdkPath, "NO_TRACKING")
        self.doNotTrack = os.path.exists(dntFile)

        # Don't track if internet connection is down
        if not self.doNotTrack:
            try:
                urlopen(self.endpoint, timeout=0.1)
            except:
                self.doNotTrack = True
                logging.debug("Analytics collection disabled due to lack of"
                              "internet connectivity")
            
        if self.doNotTrack:
            return
        
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
    def _getSDKVersion(self):
        """ Get the SDK version """
        try:
            from VersionGenerated import SDK_VERSION
            return SDK_VERSION
        except:
            return "'Development'"
        
        
    ####################################################################
    def postEvent(self, category, action, label, value=None):
        """ Send an event to the analytics collection server. 
        
        We are being a little un-orthodox with how we use the fields in the
        event and are hijacking some of the fields for alternature purposes:
        
        Campaign Name ('cn'): We are using this to represent the operating
        system as returned by python.platform(). We tried putting this into the
        user-agent string but it isn't picked up by the Google Analytics web 
        UI for some reason - perhaps it's the wrong format for that purpose. 
        
        Campaign Source ('cs'): We are also copying the client id ('cid') to
        this field. The 'cid' field is not accessible from the web UI but the
        'cs' field is. 
        
        Campaign Keyword ('ck'): We are using this to store the python version. 
        
        
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
        data['cid'] = self.clientId
        
        # TODO: Set this to PEBBLE-INTERNAL or PEBBLE-AUTOMATED as appropriate
        data['cn'] = self.osStr
        data['cs'] = self.clientId
        data['ck'] = platform.python_version()
        
        # Generate an event
        data['t'] = 'event'
        data['ec'] = category
        data['ea'] = action
        data['el'] = label
        if value:
            data['ev'] = value
        else:
            data['ev'] = 0
            
        # Convert all strings to utf-8
        for key,value in data.items():
            if isinstance(value, basestring):
                data[key] = value.encode('utf-8')
                
        headers = {
                'User-Agent': self.userAgent
                } 
        
        # We still build up the request but just don't send it if
        #  doNotTrack is on. Building it up allows us to still generate
        #  debug logging messages to see the content we would have sent
        if self.doNotTrack:
            logging.debug("Not sending analytics - tracking disabled") 
        else:
            request = Request(self.endpoint,
                          data=urlencode(data),
                          headers = headers)
        
            try:
                urlopen(request, timeout=0.1)
            except Exception as e:
                # Turn off tracking so we don't incur a delay on subsequent
                #  events in this same session. 
                self.doNotTrack = True
                logging.debug("Exception occurred sending analytics: %s" %
                              str(e))
                logging.debug("Disabling analytics due to intermittent "
                              "connectivity")
        
        # Debugging output?
        dumpDict = dict(data)
        for key in ['ec', 'ea', 'el', 'ev']:
            dumpDict.pop(key, None)
        logging.debug("[Analytics] header: %s, data: %s"  
                      "\ncategory: %s"  
                      "\naction: %s"    
                      "\nlabel: %s"     
                      "\nvalue: %s" % 
                      (headers, str(dumpDict), 
                       data['ec'], data['ea'], data['el'], data['ev']))
                      
    

####################################################################
# Our public functions for posting events to analytics
def cmdSuccessEvt(cmdName):
    """ Sent when a pebble.py command succeeds with no error 
    
    Parameters:
    --------------------------------------------------------
    cmdName: name of the pebble command that succeeded (build. install, etc.)
    """
    _Analytics.get().postEvent(category='pebbleCmd', action=cmdName, 
                              label='success')


def missingToolsEvt():
    """ Sent when we detect that the ARM tools have not been installed 
    
    Parameters:
    --------------------------------------------------------
    cmdName: name of the pebble command that failed (build. install, etc.)
    reason: description of error (missing compiler, compilation error, 
                outdated project, app too big, configuration error, etc.)
    """
    _Analytics.get().postEvent(category='install', action='tools', 
               label='fail: The compiler/linker tools could not be found')
    

def missingPythonDependencyEvt(text):
    """ Sent when pebble.py fails to launch because of a missing python
        dependency. 
    
    Parameters:
    --------------------------------------------------------
    text: description of missing dependency
    """
    _Analytics.get().postEvent(category='install', action='import', 
               label='fail: missing import: %s' % (text))


def cmdFailEvt(cmdName, reason):
    """ Sent when a pebble.py command fails  during execution 
    
    Parameters:
    --------------------------------------------------------
    cmdName: name of the pebble command that failed (build. install, etc.)
    reason: description of error (missing compiler, compilation error, 
                outdated project, app too big, configuration error, etc.)
    """
    _Analytics.get().postEvent(category='pebbleCmd', action=cmdName, 
               label='fail: %s' % (reason))
    

def codeSizeEvt(uuid, segSizes):
    """ Sent after a successful build of a pebble app to record the app size
    
    Parameters:
    --------------------------------------------------------
    uuid: application's uuid
    segSizes: a dict containing the size of each segment
                    i.e. {"text": 490, "bss": 200, "data": 100}    
    """
    totalSize = sum(segSizes.values())
    _Analytics.get().postEvent(category='appCode', action='totalSize', 
               label=uuid, value = totalSize)


def codeLineCountEvt(uuid, lineCount):
    """ Sent after a successful build of a pebble app to record the number of
    lines of source code in the app
    
    Parameters:
    --------------------------------------------------------
    uuid: application's uuid
    lineCount: number of lines of source code
    """
    _Analytics.get().postEvent(category='appCode', action='lineCount', 
               label=uuid, value = lineCount)


def codeHasJavaScriptEvt(uuid, hasJS):
    """ Sent after a successful build of a pebble app to record whether or not
    this app has javascript code in it
    
    Parameters:
    --------------------------------------------------------
    uuid: application's uuid
    hasJS: True if this app has JavaScript in it
    """
    _Analytics.get().postEvent(category='appCode', action='hasJavaScript', 
               label=uuid, value = 1 if hasJS else 0)


def resSizesEvt(uuid, resCounts, resSizes):
    """ Sent after a successful build of a pebble app to record the sizes of
    the resources
    
    Parameters:
    --------------------------------------------------------
    uuid: application's uuid
    resCounts: a dict containing the number of resources of each type
                    i.e. {"image": 4, "font": 2, "raw": 1}
    resSizes: a dict containing the size of resources of each type
                    i.e. {"image": 490, "font": 200, "raw": 100}    
    """
    totalSize = sum(resSizes.values())
    totalCount = sum(resCounts.values())
    _Analytics.get().postEvent(category='appResources', action='totalSize', 
               label=uuid, value = totalSize)
    _Analytics.get().postEvent(category='appResources', action='totalCount', 
               label=uuid, value = totalCount)
    
    for key in resSizes.keys():
        _Analytics.get().postEvent(category='appResources', 
                action='%sSize' % (key), label=uuid, value = resSizes[key])
        _Analytics.get().postEvent(category='appResources', 
                action='%sCount' % (key), label=uuid, value = resCounts[key])
        



####################################################################
if __name__ == '__main__':
    _Analytics.get().postEvent('newCategory', 'newAction', 'newLabel')
    


