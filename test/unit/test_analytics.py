import contextlib
import imp
import os
import random
import re
import shutil
import sys
import tempfile
import unittest
import urllib2
import urlparse
import argparse
from mock import patch, MagicMock


# Allow us to run even if not at the root libpebble directory.
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir) 
import pebble.PblAnalytics

# Our command line arguments are stored here by the main logic 
g_cmd_args = None

@contextlib.contextmanager
def temp_chdir(path):
    """ Convenience function for setting and restoring current working directory
    
    Usage:
         with temp_chdir(new_path):
            do_something()
    """
    starting_directory = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(starting_directory)



class TestAnalytics(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        """ Load in the main pebble shell module """
        global root_dir
        pebble_shell = imp.load_source('pebble_shell', 
                                       os.path.join(root_dir, 'pebble.py'))
        from pebble_shell import PbSDKShell
        self.p_sh = PbSDKShell()
        
        # What directory is our data in?
        self.data_dir = os.path.join(os.path.dirname(__file__), 
                                     'analytics_data')
        
        # Create a temp directory to use
        self.tmp_dir = tempfile.mkdtemp()
        
        # Get command line options
        global g_cmd_args
        if g_cmd_args is not None:
            self._debug = g_cmd_args.debug
        else:
            self._debug = False
        
    
    @classmethod
    def tearDownClass(self):
        """ Clean up after all tests """
        
        # Remove our temp directory
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        

    def use_project(self, project_name):
        """ Copies project_name from the analytics_data subdirectory to a
        new temp directory, sets that as the current working dir, and returns 
        that path. 
        
        Parameters:
        -------------------------------------------------------------------
        project_name:     name of the project
        retval: path to project after copied into a temp location
        """
        working_dir = os.path.join(self.tmp_dir, project_name)
        if os.path.exists(working_dir):
            shutil.rmtree(working_dir)
        shutil.copytree(os.path.join(self.data_dir, project_name), 
                        working_dir)
        print "Running '%s' project in directory %s" % (project_name, 
                                                        working_dir)
        return working_dir


    
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
    
    def assert_evt(self, mock_urlopen, items_filter):
        """ Walk through all the calls to our mock urlopen() and look for one 
        that satisfies items_filter, which is a dict with the key/value pairs we
        need to satisfy. The values are regular expressions.
        
        If not found, raise an assertion
        
        Parameters:
        -------------------------------------------------------------------
        mock_urlopen: the mock urlopen instance
        items_filter: dict with desired key/value pairs
        """
        (header, data) = self.find_evt(mock_urlopen, items_filter)
        self.assertTrue(header is not None, "Did not find expected event "
                        "matching constraints: %s" % (str(items_filter)))
        

    @patch('pebble.PblAnalytics.urlopen')
    def test_invalid_project(self, mock_urlopen):
        """ Test that we get the correct analytics produced when we run \
        a pebble command in an invalid project directory. 
        """

        sys.argv = ['pebble', '--debug', 'clean' ]
        retval = self.p_sh.main()

        # Verify that we sent an invalid project event
        self.assert_evt(mock_urlopen,
            {'ec': 'pebbleCmd', 'ea': 'clean', 
             'el': 'fail: invalid project'})


    @patch('pebble.PblAnalytics.urlopen')
    def test_clean_success(self, mock_urlopen):
        """ Test for success event with the 'clean' command """
        
        # Copy the desired project to temp location
        working_dir = self.use_project('good_c_app')
        
        with temp_chdir(working_dir):
            if self._debug:
                sys.argv = ['pebble', '--debug', 'clean' ]
            else:
                sys.argv = ['pebble', 'clean' ]
            retval = self.p_sh.main()

        # Verify that we sent a success event
        self.assert_evt(mock_urlopen,
            {'ec': 'pebbleCmd', 'ea': 'clean', 'el': 'success'})
        

    @patch('pebble.PblAnalytics.urlopen')
    def test_build_success_c_app(self, mock_urlopen):
        """ Test that we send the correct events after building a C app """
        
        # Copy the desired project to temp location
        working_dir = self.use_project('good_c_app')
        uuid = '19aac3eb-870b-47fb-a708-0810edc4322e'
        
        with temp_chdir(working_dir):
            if self._debug:
                sys.argv = ['pebble', '--debug', 'build' ]
            else:
                sys.argv = ['pebble', 'build' ]
            retval = self.p_sh.main()

        # Verify that we sent the correct events
        self.assert_evt(mock_urlopen,
            {'ec': 'pebbleCmd', 'ea': 'build', 'el': 'success'})
        
        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'totalSize', 'el': uuid, 'ev': '8.*'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appResources', 'ea': 'totalSize', 'el': uuid, 'ev': '0'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appResources', 'ea': 'totalCount', 'el': uuid, 'ev': '0'})

        for name in ['raw', 'image', 'font']:
            self.assert_evt(mock_urlopen,
                {'ec': 'appResources', 'ea': '%sSize' % (name), 'el': uuid, 
                 'ev': '0'})
    
            self.assert_evt(mock_urlopen,
                {'ec': 'appResources', 'ea': '%sCount' % (name), 'el': uuid, 
                 'ev': '0'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'cLineCount', 'el': uuid, 'ev': '60'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'jsLineCount', 'el': uuid, 'ev': '0'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'hasJavaScript', 'el': uuid, 'ev': '0'})



    @patch('pebble.PblAnalytics.urlopen')
    def test_build_success_js_app(self, mock_urlopen):
        """ Test that we send the correct events after building a JS app """
        
        # Copy the desired project to temp location
        working_dir = self.use_project('good_js_app')
        uuid = '74460383-8a0f-4bb6-971f-8937c2ed4441'
        
        with temp_chdir(working_dir):
            if self._debug:
                sys.argv = ['pebble', '--debug', 'build' ]
            else:
                sys.argv = ['pebble', 'build' ]
            retval = self.p_sh.main()

        # Verify that we sent the correct events
        self.assert_evt(mock_urlopen,
            {'ec': 'pebbleCmd', 'ea': 'build', 'el': 'success'})
        
        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'totalSize', 'el': uuid, 'ev': '15..'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appResources', 'ea': 'totalSize', 'el': uuid, 'ev': '38..'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appResources', 'ea': 'totalCount', 'el': uuid, 'ev': '4'})

        sizes = {'raw': '0', 'image': '3888', 'font': '0'}
        counts = {'raw': '0', 'image': '4', 'font': '0'}
        for name in ['raw', 'image', 'font']:
            self.assert_evt(mock_urlopen,
                {'ec': 'appResources', 'ea': '%sSize' % (name), 'el': uuid, 
                 'ev': sizes[name]})
    
            self.assert_evt(mock_urlopen,
                {'ec': 'appResources', 'ea': '%sCount' % (name), 'el': uuid, 
                 'ev': counts[name]})

        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'cLineCount', 'el': uuid, 'ev': '136'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'jsLineCount', 'el': uuid, 'ev': '107'})

        self.assert_evt(mock_urlopen,
            {'ec': 'appCode', 'ea': 'hasJavaScript', 'el': uuid, 'ev': '1'})





#############################################################################
def _getTestList():
  """ Get the list of tests that can be run from this module"""
  suiteNames = ['TestAnalytics']
  testNames = []
  for suite in suiteNames:
    for f in dir(eval(suite)):
      if f.startswith('test'):
        testNames.append('%s.%s' % (suite, f))

  return testNames


if __name__ == '__main__':
    usage_string = "%(prog)s [options] [-- unittestoptions] " \
                "[suitename.testname | suitename]"
                
    help_string = """Run Analytics tests.
    
Examples:
    python %(prog)s --help      # to see this help message
    python %(prog)s -- --help   # to see all unittest options
    python %(prog)s --debug  TestAnalytics 
    python %(prog)s --debug  -- --failfast TestAnalytics  
    python %(prog)s  TestAnalytics.test_build_success
     
Available suitename.testnames: """     
    all_tests = _getTestList()
    for test in all_tests:
        help_string += "\n   %s" % (test)
    
    parser = argparse.ArgumentParser(description = help_string,
                    formatter_class=argparse.RawTextHelpFormatter,
                    usage=usage_string)
    parser.add_argument('ut_args', metavar='arg', type=str, nargs='*', 
                        help=' arguments for unittest module')
    parser.add_argument('-d', '--debug', action='store_true', 
                        help=' run with debug output on')
    
    args = parser.parse_args()
    g_cmd_args = args

    unittest.main(argv=['unittest'] + args.ut_args)
