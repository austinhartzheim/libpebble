import sh, os
import websocket
import logging
import time
from multiprocessing import Process
from autobahn.websocket import *
from PblCommand import PblCommand
import pebble as libpebble
from EchoServerProtocol import *

def start_pebble_server():
  factory = WebSocketServerFactory("ws://localhost:{}".format(libpebble.DEFAULT_PEBBLE_PORT))
  factory.protocol = EchoServerProtocol
  factory.setProtocolOptions(allowHixie76 = True)
  listenWS(factory)
  reactor.run()

class LibPebbleCommand(PblCommand):
  def configure_subparser(self, parser):
    pass

  def run(self, args):
    try:
      ws = websocket.create_connection("ws://localhost:{}".format(libpebble.DEFAULT_PEBBLE_PORT))
      ws.close()
    except:
      logging.warn("Didn't find a websocket server. Creating one...")
      logging.warn("Hint: Create a long running server with 'pb-sdk.py server' command.")
      p = Process(target=start_pebble_server, args=())
      p.daemon = True
      p.start()
      time.sleep(3)

    self.pebble = libpebble.Pebble(using_lightblue=False, pair_first=False, using_ws=True)

class PblServerCommand(LibPebbleCommand):
    name = 'server'
    help = 'Run a websocket server to keep the connection to your phone and Pebble opened.'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)

    def run(self, args):
        logging.info("Starting a Pebble WS server on port {}".format(libpebble.DEFAULT_PEBBLE_PORT))
        logging.info("Type Ctrl-C to interrupt.")
        start_pebble_server()

class PblPingCommand(LibPebbleCommand):
  name = 'ping'
  help = 'Ping your Pebble project to your watch'

  def configure_subparser(self, parser):
    PblCommand.configure_subparser(self, parser)

  def run(self, args):
    LibPebbleCommand.run(self, args)
    self.pebble.ping(cookie=0xDEADBEEF)


class PblInstallCommand(LibPebbleCommand):
  name = 'install'
  help = 'Install your Pebble project to your watch'

  def configure_subparser(self, parser):
    PblCommand.configure_subparser(self, parser)
    parser.add_argument('bundle', type=str)

  def run(self, args):
    LibPebbleCommand.run(self, args)
    self.pebble.reinstall_app(args.bundle, True)
    logging.info("App installed")


class PblListCommand(LibPebbleCommand):
  name = 'list'
  help = 'List the apps installed on your watch'

  def configure_subparser(self, parser):
    PblCommand.configure_subparser(self, parser)

  def run(self, args):
    LibPebbleCommand.run(self, args)

    apps = self.pebble.get_appbank_status()
    if apps is not False:
        for app in apps['apps']:
            logging.info('[{}] {}'.format(app['index'], app['name']))
    else:
        logging.info("No apps.")


class PblRemoveCommand(LibPebbleCommand):
  name = 'rm'
  help = 'Remove an app from your watch'

  def configure_subparser(self, parser):
    PblCommand.configure_subparser(self, parser)
    parser.add_argument('bank_id', type=int, help="The bank id of the app to remove (between 1 and 8)")

  def run(self, args):
      LibPebbleCommand.run(self, args)

      for app in self.pebble.get_appbank_status()['apps']:
          if app['index'] == args.bank_id:
              self.pebble.remove_app(app["id"], app["index"])
              logging.info("App removed")
              return 0
