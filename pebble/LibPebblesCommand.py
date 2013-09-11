import fnmatch
import logging
import os
import time
import sh
import websocket

import pebble as libpebble

from autobahn.websocket import *
from EchoServerProtocol import *
from PblCommand import PblCommand

class LibPebbleCommand(PblCommand):
    def configure_subparser(self, parser):
        pass

    def run(self, args):
        echo_server_start(libpebble.DEFAULT_WEBSOCKET_PORT)
        # FIXME: This sleep is longer than the phone's reconnection interval (2s), to give it time to connect.
        sleep(2.5)
        self.pebble = libpebble.Pebble()
        self.pebble.connect_via_websocket(args.host)

class PblServerCommand(LibPebbleCommand):
    name = 'server'
    help = 'Run a websocket server to keep the connection to your phone and Pebble opened.'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)

    def run(self, args):
        logging.info("Starting a Pebble WS server on port {}".format(libpebble.DEFAULT_WEBSOCKET_PORT))
        logging.info("Type Ctrl-C to interrupt.")
        echo_server_start(libpebble.DEFAULT_WEBSOCKET_PORT, blocking=True)

class PblPingCommand(LibPebbleCommand):
    name = 'ping'
    help = 'Ping your Pebble project to your watch'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser, is_connect=True)

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.pebble.ping(cookie=0xDEADBEEF)


class PblInstallCommand(LibPebbleCommand):
    name = 'install'
    help = 'Install your Pebble project to your watch'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser, is_connect=True)
        parser.add_argument('pbw_path', type=str, nargs='?')
        parser.add_argument('--logs', action='store_true', help='Display logs after installing the app')

    def find_pbw_path(self, args):
        for root, dirnames, filenames in os.walk('build'):
            for filename in fnmatch.filter(filenames, '*.pbw'):
                return os.path.join(root, filename)

        return 'build/{}.pbw'.format(os.path.basename(os.getcwd()))

    def run(self, args):
        if not args.pbw_path:
            args.pbw_path = self.find_pbw_path(args)

        LibPebbleCommand.run(self, args)
        self.pebble.install_app_ws(args.pbw_path)

        if args.logs:
            logging.info('Displaying logs ... Ctrl-C to interrupt.')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                return


class PblListCommand(LibPebbleCommand):
    name = 'list'
    help = 'List the apps installed on your watch'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser, is_connect=True)

    def run(self, args):
        LibPebbleCommand.run(self, args)

        try:
            response = self.pebble.get_appbank_status()
            apps = response['apps']
            if len(apps) == 0:
                logging.info("No apps installed.")
            for app in apps:
                logging.info('[{}] {}'.format(app['index'], app['name']))
        except:
            logging.error("Error getting apps list.")
            return 1

class PblRemoveCommand(LibPebbleCommand):
    name = 'rm'
    help = 'Remove an app from your watch'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser, is_connect=True)
        parser.add_argument('bank_id', type=int, help="The bank id of the app to remove (between 1 and 8)")

    def run(self, args):
        LibPebbleCommand.run(self, args)

        for app in self.pebble.get_appbank_status()['apps']:
            if app['index'] == args.bank_id:
                self.pebble.remove_app(app["id"], app["index"])
                logging.info("App removed")
                return 0

        logging.info("No app found in bank %u" % args.bank_id)
        return 1


class PblLogsCommand(LibPebbleCommand):
    name = 'logs'
    help = 'Continuously displays logs from the watch'

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser, is_connect=True)

    def run(self, args):
        LibPebbleCommand.run(self, args)

        logging.info('Displaying logs ... Ctrl-C to interrupt.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return
