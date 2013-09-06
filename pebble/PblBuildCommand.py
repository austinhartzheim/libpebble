import sh, os
from PblCommand import PblCommand

class PblWafCommand(PblCommand):
    """ Helper class for build commands that execute waf """

    def waf_path(self, args):
        return os.path.join(os.path.join(self.sdk_path(args), 'Pebble'), 'waf')

class PblBuildCommand(PblWafCommand):
    name = 'build'
    help = 'Build your Pebble project'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)

    def run(self, args):
        os.system(self.waf_path(args) + " configure build")

class PblCleanCommand(PblWafCommand):
    name = 'clean'
    help = 'Clean your Pebble project'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)

    def run(self, args):
        os.system(self.waf_path(args) + " distclean")

