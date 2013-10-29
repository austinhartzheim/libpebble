#!/usr/bin/env python

from urllib2 import urlopen, Request
from urllib import urlencode

import datetime
import time


TRACKING_ID = 'UA-30638158-7'
ENDPOINT = 'https://www.google-analytics.com/collect'

####################################################################
def postEvent(category, action, label, value=None):
    """ Send an event to the analytics collection server. 
    
    """
    data = {}
    data['v'] = 1
    data['tid'] = TRACKING_ID
    
    #TODO: generate this from host information
    data['cid'] = '35009a79-1a05-49d7-b876-2b884d0f825b'
    
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
            
    request = Request(ENDPOINT,
        data=urlencode(data),
        headers = {
            'User-Agent': 'Pebble SDK Analytics (Python)'
        })
    urlopen(request)
    
    


if __name__ == '__main__':
  
    postEvent('newCategory', 'newAction', 'newLabel')
    


