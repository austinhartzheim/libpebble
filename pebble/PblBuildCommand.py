import sh, os, subprocess
from PblCommand import PblCommand

class PblWafCommand(PblCommand):
    """ Helper class for build commands that execute waf """

    waf_cmds = ""

    def waf_path(self, args):
        return os.path.join(os.path.join(self.sdk_path(args), 'Pebble'), 'waf')

    def run(self, args):
        return subprocess.call(self.waf_path(args) + " " + self.waf_cmds, shell=True)

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
