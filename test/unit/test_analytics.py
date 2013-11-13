import random
import unittest
import sys
import imp
from mock import patch, MagicMock
import pebble.PblAnalytics
import urllib2
import urlparse
import re

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        """ Load in the main pebble shell module """
        pebble_shell = imp.load_source('pebble_shell', 'pebble.py')
        from pebble_shell import PbSDKShell
        self.p_sh = PbSDKShell()
    
    
    def find_evt(self, mock_urlopen, items_filter):
        """ Walk through all the calls to our mock urlopen() and look for one 
        that satisfies items_filter, which is a dict with the key/value pairs we
        need to satisfy. The values are regular expressions.
        
        Parameters:
        -------------------------------------------------------------------
        mock_urlopen: the mock urlopen instance
        items_filter: dict with desired key/value pairs
        retval: (header, data) if event was found
                (None, None) if not found
        """

        found = False
        for call in mock_urlopen.call_args_list:
            req = call[0][0]
            if isinstance(req, urllib2.Request):
              header = req.headers
              data = urlparse.parse_qs(req.get_data())
              matches = True
              for (key, value) in items_filter.items():
                if not re.match(value, data[key][0]):
                  matches = False
                  break
              if matches:
                  return (header, data)

        return (None, None)
        

    def assert_cmd_fail_evt_present(self, mock_urlopen, cmd_name, reason):
        """ Walk through all the calls to urlopen() and insure that a 
        'command fail' event was sent out with the given reason 
        
        Parameters:
        -------------------------------------------------------------------
        mock_urlopen: the mock urlopen instance
        cmd_name: the command that should have failed
        reason: the reason text
        """
        
        (header, data) = self.find_evt(mock_urlopen,
            {'ec': '^pebbleCmd$', 'ea': '^%s$' % (cmd_name), 
             'el': '^fail: %s' % (reason)})

        self.assertTrue(data is not None, "Didn't send expected '%s' event "
                "with %s command" % (reason, cmd_name))


    @patch('pebble.PblAnalytics.urlopen')
    def test_invalid_project(self, mock_urlopen):
        """ Test that we get the correct analytics produced when we run
        a pebble command in an invalid project directory """
        
        sys.argv = ['pebble', '--debug', 'clean' ]
        retval = self.p_sh.main()

        # Verify that we sent an invalid project event
        self.assert_cmd_fail_evt_present(mock_urlopen, 'clean',
                        'invalid project')


    def ZZZ1test_invalid_project(self):
        """ Test that we get the correct analytics produced when we run
        a pebble command in an invalid project directory """
        
        sys.argv = ['pebble', '--debug', 'clean' ]
        with patch('pebble.PblAnalytics.urlopen') as my_mock:
            retval = self.p_sh.main()
            import pdb; pdb.set_trace()
            print my_mock





if __name__ == '__main__':
    unittest.main()
