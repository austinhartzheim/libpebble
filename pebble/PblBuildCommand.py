import sh, os, subprocess
from PblCommand import PblCommand
from PblProjectCreator import requires_project_dir
from LibPebblesCommand import NoCompilerException, BuildErrorException

class PblWafCommand(PblCommand):
    """ Helper class for build commands that execute waf """

    waf_cmds = ""

    def waf_path(self, args):
        return os.path.join(os.path.join(self.sdk_path(args), 'Pebble'), 'waf')

    @requires_project_dir
    def run(self, args):
        os.environ['PATH'] = "{}:{}".format(os.path.join(self.sdk_path(args), 
                                "arm-cs-tools", "bin"), os.environ['PATH'])
        retval = subprocess.call(self.waf_path(args) + " " + self.waf_cmds, 
                                 shell=True)
        
        # If an error occurred, do some sleuthing to determine a cause. This 
        # allows the caller to post more useful information to analytics. 
        # Note that we tried capturing stdout and stderr using Popen(), but 
        # then you lose the nice color coding produced when the command outputs
        # to a terminal directly. 
        if (retval):
            try:
                logOutput = open(os.path.join("build", "config.log")).read()
            except:
                logOutput = ""
            
            # Look for common problems
            if "Could not determine the compiler version" in logOutput:
                raise NoCompilerException
            
            else:
                raise BuildErrorException
            
            
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
