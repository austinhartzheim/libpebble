import fnmatch
import logging
import os
import sh
import time

from pebblecomm import pebble as libpebble

from PblCommand import PblCommand
import PblAnalytics

PEBBLE_PHONE_ENVVAR='PEBBLE_PHONE'
PEBBLE_BTID_ENVVAR='PEBBLE_BTID'
PEBBLE_QEMU_ENVVAR='PEBBLE_QEMU'

class ConfigurationException(Exception):
    pass

class NoCompilerException(Exception):
    """ Returned by PblBuildCommand if we couldn't find the ARM tools """
    pass

class BuildErrorException(Exception):
    """ Returned by PblBuildCommand if there was a compile or link error """
    pass

class AppTooBigException(Exception):
    """ Returned by PblBuildCommand if the app is too big"""
    pass


class LibPebbleCommand(PblCommand):

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)
        parser.add_argument('--phone', type=str,
                help='When using Developer Connection, the IP address or hostname of your phone. Can also be provided through %s environment variable.' % PEBBLE_PHONE_ENVVAR)
        parser.add_argument('--pebble_id', type=str,
                help='When using a direct BT connection, the watch\'s Bluetooth ID (e.g. DF38 or 01:23:45:67:DF:38). Can also be provided through %s environment variable.' % PEBBLE_BTID_ENVVAR)
        parser.add_argument('--qemu', type=str,
                help='When connecting to the emulator, the hostname:port of the emulator. Can also be provided through %s environment variable.' % PEBBLE_QEMU_ENVVAR)
        parser.add_argument('--pair', action="store_true", help="When using a direct BT connection, attempt to pair the watch automatically")
        parser.add_argument('--verbose', action="store_true", default=False,
                            help='Prints received system logs in addition to APP_LOG')

    def run(self, args):
        # e.g. needed to de-sym crashes on `pebble logs`
        self.add_arm_tools_to_path(args)

        # Only use the envrionment variables as defaults if no command-line arguments were specified
        # ...allowing you to leave the envrionment var(s) set at all times
        if not args.phone and not args.pebble_id and not args.qemu:
            args.phone = os.getenv(PEBBLE_PHONE_ENVVAR)
            args.pebble_id = os.getenv(PEBBLE_BTID_ENVVAR)
            args.qemu = os.getenv(PEBBLE_QEMU_ENVVAR)

        if not args.phone and not args.pebble_id and not args.qemu:
            raise ConfigurationException("No method specified to connect to watch\n- To use "
                  "Developer Connection, argument --phone is required (or set the %s environment "
                  "variable)\n- To use a direct BT connection, argument --pebble_id is required "
                  "(or set the %s environment variable)\n- To use a QEMU connection, argument "
                  "--qemu is required (or set the %s environment variable)" % (PEBBLE_PHONE_ENVVAR,
                   PEBBLE_BTID_ENVVAR, PEBBLE_QEMU_ENVVAR))

        num_args = bool(args.phone) + bool(args.pebble_id) + bool(args.qemu)
        if num_args > 1:
            raise ConfigurationException("You must specify only one method to connect to the watch "
                 " - either Developer Connection (with --phone/%s), direct via Bluetooth (with "
                 "--pebble_id/%s), or via QEMU (with --qemu/%s)" % (PEBBLE_PHONE_ENVVAR,
                 PEBBLE_BTID_ENVVAR, PEBBLE_QEMU_ENVVAR))

        self.pebble = libpebble.Pebble(args.pebble_id)
        self.pebble.set_print_pbl_logs(args.verbose)
        if args.phone:
            self.pebble.connect_via_websocket(args.phone)
        elif args.pebble_id:
            self.pebble.connect_via_lightblue(pair_first=args.pair)
        elif args.qemu:
            self.pebble.connect_via_qemu(args.qemu)

    def tail(self, interactive=False, skip_enable_app_log=False):
        if not skip_enable_app_log:
            self.pebble.app_log_enable()
        if interactive:
            logging.info('Entering interactive mode ... Ctrl-D to interrupt.')
            def start_repl(pebble):
                import code
                import readline
                import rlcompleter

                readline.set_completer(rlcompleter.Completer(locals()).complete)
                readline.parse_and_bind('tab:complete')
                code.interact(local=locals())
            start_repl(self.pebble)
        else:
            logging.info('Displaying logs ... Ctrl-C to interrupt.')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print "\n"
        self.pebble.app_log_disable()

class PblPingCommand(LibPebbleCommand):
    name = 'ping'
    help = 'Ping your Pebble project to your watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.pebble.ping(cookie=0xDEADBEEF)

class PblInstallCommand(LibPebbleCommand):
    name = 'install'
    help = 'Install your Pebble project to your watch'

    def get_bundle_path(self):
        return 'build/{}.pbw'.format(os.path.basename(os.getcwd()))

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)
        parser.add_argument('bundle_path', type=str, nargs='?', default=self.get_bundle_path(), help='Path to the .pbw or .pbz to install (e.g. build/*.pbw, default %s)' % self.get_bundle_path())
        parser.add_argument('--logs', action='store_true', help='Display logs after installing the bundle')
        parser.add_argument('--direct', action='store_true', help='Install directly on watch. Default is to send the'
                'complete bundle to the phone and have it send the pieces of the bundle to the watch. '
                'WARNING: This option won\'t work for PBWs with javascript in them.')

    def run(self, args):
        LibPebbleCommand.run(self, args)

        if not os.path.exists(args.bundle_path):
            logging.error("Could not find bundle <{}> for install.".format(args.bundle_path))
            return 1

        if args.logs:
            self.pebble.app_log_enable()

        if args.bundle_path.lower().endswith(".pbw"):
            success = self.pebble.install_app(args.bundle_path, direct=args.direct)
        elif args.bundle_path.lower().endswith(".pbz"):
            success = self.pebble.install_firmware(args.bundle_path)
        else:
            logging.error("You must specify either a .pbw or .pbz to install")
            return 1

        if self.pebble.is_phone_info_available():
            # Send the phone OS version to analytics
            phoneInfoStr = self.pebble.get_phone_info()
            PblAnalytics.phone_info_evt(phoneInfoStr=phoneInfoStr)

        if success and args.logs:
            self.tail(skip_enable_app_log=True)

class PblListCommand(LibPebbleCommand):
    name = 'list'
    help = 'List the apps installed on your watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

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
        LibPebbleCommand.configure_subparser(self, parser)
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

class PblCurrentAppCommand(LibPebbleCommand):
    name = 'current'
    help = 'Get the uuid and name of the current app'

    def run(self, args):
        LibPebbleCommand.run(self, args)

        uuid = self.pebble.current_running_uuid()
        uuid_hex = uuid.translate(None, '-')
        if not uuid:
            return
        elif int(uuid_hex, 16) == 0:
            print "System"
            return

        print uuid
        d = self.pebble.describe_app_by_uuid(uuid_hex)
        if not isinstance(d, dict):
            return
        print "Name: %s\nCompany: %s\nVersion: %d" % (d.get("name"), d.get("company"), d.get("version"))
        return

class PblListUuidCommand(LibPebbleCommand):
    name = 'uuids'
    help = 'List the uuids and names of installed apps'

    def run(self, args):
        LibPebbleCommand.run(self, args)

        uuids = self.pebble.list_apps_by_uuid()
        if len(uuids) is 0:
            logging.info("No apps installed.")

        for uuid in uuids:
            uuid_hex = uuid.translate(None, '-')
            description = self.pebble.describe_app_by_uuid(uuid_hex)
            if not description:
                continue

            print '%s - %s' % (description["name"], uuid)

class PblScreenshotCommand(LibPebbleCommand):
    name = 'screenshot'
    help = 'take a screenshot of the pebble'

    def run(self, args):
        LibPebbleCommand.run(self, args)

        logging.info("Taking screenshot...")
        def progress_callback(amount):
            logging.info("%.2f%% done..." % (amount*100.0))

        image = self.pebble.screenshot(progress_callback)
        name = time.strftime("pebble-screenshot_%Y-%m-%d_%H-%M-%S.png")
        try:
            image.save(name)
        except TypeError as e:
            # NOTE: Some customers have experienced the following exception
            #  during image.save: "TypeError: function takes at most 4 arguments
            #   (6 given)". This is due to having the Pillow python modules
            #   call into PIL compiled binaries. This apparently can happen
            #   after an upgrade to MacOS 10.9 or XCode 5 depending on which
            #   versions of PIL and/or Pillow were installed before the upgrade.
            if "function takes at most" in e.message:
                logging.error("CONFLICT DETECTED: We detected two conflicting "
                  "installations of the same python package for image "
                  "processing (PIL and Pillow) and could not proceed. In order "
                  "to clear up this conflict, please run the following commands "
                  "from a terminal window and try again: "
                  "\n    pip uninstall PIL"
                  "\n    pip install --user Pillow"
                  "\n")
                raise Exception("Conflicting PIL and Pillow packages")
            else:
                raise
        logging.info("Screenshot saved to %s" % name)

        # Open up the image in the user's default image viewer. For some
        # reason, this doesn't seem to open it up in their webbrowser,
        # unlike how it might appear. See
        # http://stackoverflow.com/questions/7715501/pil-image-show-doesnt-work-on-windows-7
        try:
            import webbrowser
            webbrowser.open(name)
        except:
            logging.info("Note: Failed to open image, you'll have to open it "
                         "manually if you want to see what it looks like ("
                         "it has still been saved, however).")


class PblCoreDumpCommand(LibPebbleCommand):
    name = 'coredump'
    help = 'get most recent core dump from the pebble'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)
        parser.add_argument('--generate', action='store_true', help='If specified, generate a core dump image on the '
                'watch. Wait for the watch to reboot and issue the coredump command again without --generate to '
                'then fetch it.')

    def run(self, args):
        LibPebbleCommand.run(self, args)

        if args.generate:
            self.pebble.reset(coredump=True);
            logging.info("Generating a coredump image and resetting the Pebble. Issue this command again without "
                         "the --generate option after the Pebble reboots in order to fetch the coredump image");
            return

        logging.info("Fetching coredump from Pebble...")
        def progress_callback(amount):
            logging.info("%.2f%% done..." % (amount*100.0))

        blob = self.pebble.coredump(progress_callback)
        name = time.strftime("pebble-coredump_%Y-%m-%d_%H-%M-%S.bin")
        if len(blob) == 0:
            logging.error("Error fetching core dump")
            return
        try:
            with open(name, 'w') as f:
                f.write(blob)
        except:
            raise

        logging.info("Core dump saved to %s" % name)


class PblLogsCommand(LibPebbleCommand):
    name = 'logs'
    help = 'Continuously displays logs from the watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.tail()

class PblReplCommand(LibPebbleCommand):
    name = 'repl'
    help = 'Launch an interactive python shell with a `pebble` object to execute methods on.'

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.tail(interactive=True)


class PblEmuTapCommand(LibPebbleCommand):
    name = 'emu_tap'
    help = 'Send a tap event to Pebble running in the emulator'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.pebble.emu_tap()


