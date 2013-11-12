import random
import unittest
import sys
import imp


class TestAnalytics(unittest.TestCase):

    def setUp(self):
        """ Load in the main pebble shell module """
        pebble_shell = imp.load_source('pebble_shell', 'pebble.py')
        from pebble_shell import PbSDKShell
        self.p_sh = PbSDKShell()


    def test_invalid_project(self):
        """ Test that we get the correct analytics produced when we run
        a pebble command in an invalid project directory """
        
        sys.argv = ['pebble', '--debug', 'clean' ]
        retval = self.p_sh.main()
        import pdb; pdb.set_trace() 
        


if __name__ == '__main__':
    unittest.main()
