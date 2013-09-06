import sh, os, subprocess
from PblCommand import PblCommand

class PblBuildCommand(PblCommand):
    name = 'build'
    help = 'Build your Pebble project'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)

    def run(self, args):
        return subprocess.call(self.waf_path(args) + " configure build", shell=True)

    def waf_path(self, args):
        return os.path.join(os.path.join(self.sdk_path(args), 'Pebble'), 'waf')
