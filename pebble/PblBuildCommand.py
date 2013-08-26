import sh, os
from PblCommand import PblCommand

class PblBuildCommand(PblCommand):
  name = 'build'
  help = 'Build your Pebble project'

  def configure_subparser(self, parser):
    parser.add_argument('--sdk', help='Path to Pebble SDK (ie: ~/pebble-dev/PebbleSDK-2.X/)')

  def run(self, args):
    waf_path = os.path.join(os.path.join(self.sdk_path(args), 'Pebble'), 'waf')
    print "Path to waf: {}".format(waf_path)
    os.system(waf_path + " configure build")

  def sdk_path(self, args):
    """
    Tries to guess the location of the Pebble SDK
    """

    if args.sdk:
      return args.sdk
    else:
      return os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
