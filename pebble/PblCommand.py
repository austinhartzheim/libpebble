import os
import sh

class PblCommand:
  name = ''
  help = ''

  def run(args):
    pass

  def configure_subparser(self, parser):
    pass

  def sdk_path(self):
    """
    Tries to guess the location of the Pebble SDK
    """
    return os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.join('..', '..')))
