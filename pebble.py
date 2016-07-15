#!/usr/bin/env python

import argparse
import logging
import sys

try:
    # NOTE: Even though we don't use websocket in this module, keep this
    #  import here for the unit tests so that they can trigger a missing
    #  python dependency event.
    import websocket
    import pebble as libpebble
    from pebble.PblProject import InvalidProjectException, OutdatedProjectException
    from pebble.PblProjectCreator   import PblProjectCreator
    from pebble.PblProjectConverter import PblProjectConverter
    from pebble.PblBuildCommand     import PblBuildCommand, PblCleanCommand, PblAnalyzeSizeCommand
    from pebble.LibPebblesCommand   import *
except Exception as e:
    logging.basicConfig(format='[%(levelname)-8s] %(message)s',
                    level = logging.DEBUG)


class PbSDKShell:
    commands = []

    def __init__(self):
        self.commands.append(PblProjectCreator())
        self.commands.append(PblProjectConverter())
        self.commands.append(PblBuildCommand())
        self.commands.append(PblCleanCommand())
        self.commands.append(PblAnalyzeSizeCommand())
        self.commands.append(PblInstallCommand())
        self.commands.append(PblPingCommand())
        self.commands.append(PblListCommand())
        self.commands.append(PblRemoveCommand())
        self.commands.append(PblCurrentAppCommand())
        self.commands.append(PblListUuidCommand())
        self.commands.append(PblLogsCommand())
        self.commands.append(PblReplCommand())
        self.commands.append(PblScreenshotCommand())
        self.commands.append(PblCoreDumpCommand())
        self.commands.append(PblEmuTapCommand())
        self.commands.append(PblEmuBluetoothConnectionCommand())
        self.commands.append(PblEmuCompassCommand())
        self.commands.append(PblEmuBatteryCommand())
        self.commands.append(PblEmuAccelCommand())
        self.commands.append(PblKillCommand())
        self.commands.append(PblWipeCommand())
        self.commands.append(PblInsertPinCommand())
        self.commands.append(PblDeletePinCommand())
        self.commands.append(PblLoginCommand())

    def _get_version(self):
        try:
            from pebble.VersionGenerated import SDK_VERSION
            return SDK_VERSION
        except:
            return "Development"

    def main(self):
        parser = argparse.ArgumentParser(description = 'Pebble SDK Shell',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--debug', action="store_true",
                            help="Enable debugging output")
        parser.add_argument('--version', action='version',
                            version='PebbleSDK %s' % self._get_version())
        subparsers = parser.add_subparsers(dest="command", title="Command",
                                           description="Action to perform")
        for command in self.commands:
            subparser = subparsers.add_parser(command.name, help = command.help)
            command.configure_subparser(subparser)
        args = parser.parse_args()

        log_level = logging.INFO
        if args.debug:
            log_level = logging.DEBUG

        logging.basicConfig(format='[%(levelname)-8s] %(message)s',
                            level = log_level)
        if log_level != logging.DEBUG:
            logging.getLogger("requests").setLevel(logging.WARNING)

        # Just in case logging was already setup, basicConfig would not
        # do anything, so set the level on the root logger
        logging.getLogger().setLevel(log_level)

        return self.run_action(args.command, args)

    def run_action(self, action, args):
        # Find the extension that was called
        command = [x for x in self.commands if x.name == args.command][0]

        start_time = time.time()
        try:
            retval = command.run(args)
            return retval

        except libpebble.PebbleError as e:
            post_event('sdk_libpebble_failed', exception=str(e))
            if args.debug:
                raise e
            else:
                logging.error(e)
                return 1

        except InvalidProjectException as e:
            post_event('sdk_run_without_project')
            logging.error("This command must be run from a Pebble project directory")
            return 1

        except OutdatedProjectException as e:
            post_event('sdk_building_outdated_project')
            logging.error("The Pebble project directory is using an outdated version of the SDK!")
            logging.error("Try running `pebble convert-project` to update the project")
            return 1

        except NoCompilerException as e:
            post_event('sdk_missing_tools')
            logging.error("The compiler/linker tools could not be found. "
                          "Ensure that the arm-cs-tools directory is present in the Pebble SDK directory (%s)" %
                          PblCommand().sdk_path(args))
            return 1

        except BuildErrorException as e:
            post_event('app_build_failed', build_time=(time.time() - start_time), type="compilation_error")
            logging.error("A compilation error occurred")
            return 1

        except AppTooBigException as e:
            post_event('app_build_failed', build_time=(time.time() - start_time), type="app_too_large")
            logging.error("The built application is too big")
            return 1

        except Exception as e:
            post_event('sdk_unhandled_exception', exception=str(e))
            logging.error(str(e))

            # Print out stack trace if in debug mode to aid in bug reporting
            if args.debug:
                raise
            return 1


def main():
    retval = PbSDKShell().main()
    if retval is None:
        retval = 0
    return retval

if __name__ == '__main__':
    sys.exit(main())
