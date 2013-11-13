import random
import unittest
import sys
import imp
from mock import patch, MagicMock
import pebble.PblAnalytics
import urllib2
import urlparse

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        """ Load in the main pebble shell module """
        pebble_shell = imp.load_source('pebble_shell', 'pebble.py')
        from pebble_shell import PbSDKShell
        self.p_sh = PbSDKShell()


    @patch('pebble.PblAnalytics.urlopen')
    def test_invalid_project(self, mock_urlopen):
        """ Test that we get the correct analytics produced when we run
        a pebble command in an invalid project directory """
        
        sys.argv = ['pebble', '--debug', 'clean' ]
        retval = self.p_sh.main()

        # Verify that we sent an invalid project event
        success = False
        for call in mock_urlopen.call_args_list:
            req = call[0][0]
            if isinstance(req, urllib2.Request):
              header = req.headers
              data = urlparse.parse_qs(req.get_data())
              if data['ec'][0] == 'pebbleCmd' and data['ea'][0] == 'clean' \
                and 'invalid project' in data['el'][0]:
                  success = True
        
        self.assertTrue(success, "Didn't send expected 'invalid project' event")


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
