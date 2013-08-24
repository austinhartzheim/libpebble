from PblCommand import PblCommand

class PblBuildCommand(PblCommand):
  name = 'build'
  help = 'Build your Pebble project'

  def configure_subparser(self, parser):
    pass

  def run(self, args):
    print "Pebble SDK is in: {}".format(self.sdk_path())
