
import logging
import sh, os, subprocess
import json

import PblAnalytics
from PblCommand import PblCommand
from PblProjectCreator import requires_project_dir
from LibPebblesCommand import (NoCompilerException, BuildErrorException,
                               AppTooBigException)

class PblWafCommand(PblCommand):
    """ Helper class for build commands that execute waf """

    waf_cmds = ""

    def waf_path(self, args):
        return os.path.join(os.path.join(self.sdk_path(args), 'Pebble'), 'waf')
    
    
    def _sendMemoryUsage(self, args, appInfo):
        """ Send app memory usage to analytics 
        
        Parameters:
        --------------------------------------------------------------------
        args: the args passed to the run() method
        appInfo: the applications appInfo
        """
        try:
            cmdArgs = [os.path.join(self.sdk_path(args), "arm-cs-tools", "bin",
                    "arm-none-eabi-size"), os.path.join("build", "pebble-app.elf")]
            pobj = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            (stdout, stderr) = pobj.communicate()
            retval = pobj.returncode
    
            if retval == 0:
                (textSize, dataSize, bssSize) = [int(x) for x in \
                                         stdout.splitlines()[1].split()[:3]]
                sizeDict = {'text': textSize, 'data': dataSize, 'bss': bssSize}
                PblAnalytics.appSizeEvt(uuid=appInfo["uuid"], 
                                        segSizes = sizeDict)
            else:
                logging.error("command line %s failed. stdout: %s, stderr: %s" %
                              cmdArgs, stdout, stderr)
        except Exception as e:
            logging.error("Exception occurred collecting memory usage: %s" %
                          str(e))


    def _sendResourceUsage(self, args, appInfo):
        """ Send app resource usage up to analytics 
        
        Parameters:
        --------------------------------------------------------------------
        args: the args passed to the run() method
        appInfo: the applications appInfo
        """
        
        try:
            
            # Collect the number and total size of each class of resource:
            resCounts = {"raw": 0, "image": 0, "font": 0}
            resSizes = {"raw": 0, "image": 0, "font": 0}
            
            for resDict in appInfo["resources"]["media"]:
                if resDict["type"] in ["png", "png-trans"]:
                    type = "image"
                elif resDict["type"] in ["font"]: 
                    type = "font"
                elif resDict["type"] in ["raw"]:
                    type = "raw"
                else:
                    raise RuntimeError("Unsupported resource type %s" % 
                                    (resDict["type"]))

                # Look for the generated blob in the build/resource directory.
                # As far as we can tell, the generated blob always starts with
                # the original filename and adds an extension to it, or (for
                # fonts), a name and extension. 
                (dirName, fileName) = os.path.split(resDict["file"])
                dirToSearch = os.path.join("build", "resources", dirName)
                found = False
                for name in os.listdir(dirToSearch):
                    if name.startswith(fileName):
                        size = os.path.getsize(os.path.join(dirToSearch, name))
                        found = True
                        break
                if not found:
                    raise RuntimeError("Could not find generated resource "
                                "corresponding to %s." % (resDict["file"]))
                    
                resCounts[type] += 1
                resSizes[type] += size
                
            # Send the stats now
            PblAnalytics.resSizesEvt(uuid=appInfo["uuid"],
                                     resCounts = resCounts,
                                     resSizes = resSizes)
            
            
             
        except Exception as e:
            logging.error("Exception occurred collecting resource usage: %s" %
                          str(e))
            
        

    @requires_project_dir
    def run(self, args):
        os.environ['PATH'] = "{}:{}".format(os.path.join(self.sdk_path(args), 
                                "arm-cs-tools", "bin"), os.environ['PATH'])
        
        cmdLine = self.waf_path(args) + " " + self.waf_cmds
        retval = subprocess.call(cmdLine, shell=True)
        
        # If an error occurred, we need to do some sleuthing to determine a
        # cause. This allows the caller to post more useful information to
        # analytics. We normally don't capture stdout and stderr using Poepn()
        # because you lose the nice color coding produced when the command
        # outputs to a terminal directly.
        #
        # But, if an error occurs, let's run it again capturing the output
        #  so we can determine the cause
          
        if (retval):
            pobj = subprocess.Popen(cmdLine.split(), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            (stdout, stderr) = pobj.communicate()
                 
            # Look for common problems
            if "Could not determine the compiler version" in stderr:
                raise NoCompilerException
            
            elif "region `APP' overflowed" in stderr:
                raise AppTooBigException
            
            else:
                raise BuildErrorException
            
        else:
            # No error building. Send up app memoyr usage and resource usage
            #  up to analytics
            # Read in the appinfo.json to get the list of resources
            appInfo = json.load(open("appinfo.json"))
            self._sendMemoryUsage(args, appInfo)
            self._sendResourceUsage(args, appInfo)
            
        return 0

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)

class PblBuildCommand(PblWafCommand):
    name = 'build'
    help = 'Build your Pebble project'
    waf_cmds = 'configure build'

class PblCleanCommand(PblWafCommand):
    name = 'clean'
    help = 'Clean your Pebble project'
    waf_cmds = 'distclean'
