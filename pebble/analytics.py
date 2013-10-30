#!/usr/bin/env python

from urllib2 import urlopen, Request
from urllib import urlencode

import datetime
import time
import logging


DEBUG = True


####################################################################
class Analytics(object):
    # This is the tracking ID assigned to Pebble for the "Pebble SDK Tool"
    #  web site (pebble.getpebble.com) 
    trackingId = 'UA-30638158-7'
    
    # This is the URL of the Google analytics server
    endpoint = 'https://www.google-analytics.com/collect'
    
    _userAgent = None
    
    @classmethod
    def userAgent(cls):
        if cls._userAgent is None:
            version = '1.0'   # TODO: fill this in
            os = 'Macintosh; Intel Mac OS X 10_9'   # TODO: fill this in
            cls._userAgent = 'Pebble SDK/%s (%s)' % (version, os) 
        return cls._userAgent
    
    @classmethod
    def clientId(cls):
        return None
        #return '35009a79-1a05-49d7-b876-2b884d0f825b'
    
    

####################################################################
def _postEvent(category, action, label, value=None):
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
    data['tid'] = Analytics.trackingId
    
    #TODO: generate this from host information
    data['cid'] = Analytics.clientId()
    
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
            'User-Agent': Analytics.userAgent()
            } 
    request = Request(Analytics.endpoint,
                      data=urlencode(data),
                      headers = headers)
    urlopen(request)
    
    # Debugging output?
    logging.debug("[Analytics] header: %s, data: %s" % (headers, data))
    
    
####################################################################
def cmdSuccessEvt(cmdName):
    _postEvent(category='pebbleCmd', action=cmdName, label='success')

def cmdFailEvt(cmdName, reason):
    _postEvent(category='pebbleCmd', action=cmdName, 
               label='fail: %s' % (reason))
    


####################################################################
if __name__ == '__main__':
    _postEvent('newCategory', 'newAction', 'newLabel')
    


