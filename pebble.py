#!/usr/bin/env python

import argparse
import logging
import sys

import pebble as libpebble
from pebble.PblProjectCreator   import PblProjectCreator, InvalidProjectException, OutdatedProjectException
from pebble.PblProjectConverter import PblProjectConverter
from pebble.PblBuildCommand     import PblBuildCommand, PblCleanCommand
from pebble.LibPebblesCommand   import *

class PbSDKShell:
    commands = []

    def __init__(self):
        self.commands.append(PblProjectCreator())
        self.commands.append(PblProjectConverter())
        self.commands.append(PblBuildCommand())
        self.commands.append(PblCleanCommand())
        self.commands.append(PblInstallCommand())
        self.commands.append(PblPingCommand())
        self.commands.append(PblListCommand())
        self.commands.append(PblRemoveCommand())
        self.commands.append(PblLogsCommand())
        self.commands.append(PblReplCommand())

    def _get_version(self):
        try:
            from pebble.VersionGenerated import SDK_VERSION
            return SDK_VERSION
        except:
            return "'Development'"

    def main(self):
        parser = argparse.ArgumentParser(description = 'Pebble SDK Shell')
        parser.add_argument('--debug', action="store_true", help="Enable debugging output")
        parser.add_argument('--version', action='version', version='PebbleSDK %s' % self._get_version())
        subparsers = parser.add_subparsers(dest="command", title="Command", description="Action to perform")
        for command in self.commands:
            subparser = subparsers.add_parser(command.name, help = command.help)
            command.configure_subparser(subparser)
        args = parser.parse_args()

        log_level = logging.INFO
        if args.debug:
            log_level = logging.DEBUG

        logging.basicConfig(format='[%(levelname)-8s] %(message)s', level = log_level)

        return self.run_action(args.command, args)

    def run_action(self, action, args):
        # Find the extension that was called
        command = [x for x in self.commands if x.name == args.command][0]

        try:
            return command.run(args)
        except libpebble.PebbleError as e:
            if args.debug:
                raise e
            else:
                logging.error(e)
                return 1
        except ConfigurationException as e:
            logging.error(e)
            return 1
        except InvalidProjectException as e:
            logging.error("This command must be run from a Pebble project directory")
            return 1
        except OutdatedProjectException as e:
            logging.error("The Pebble project directory is using an outdated version of the SDK!")
            logging.error("Try running `pb-sdk convert-project` to update the project")
            return 1


if __name__ == '__main__':
    retval = PbSDKShell().main()
    if retval is None:
        retval = 0
    sys.exit(retval)

