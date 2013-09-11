import os
import pebble as libpebble

class PblCommand:
    name = ''
    help = ''

    def run(args):
        pass

    def configure_subparser(self, parser, is_connect=False):
        parser.add_argument('--sdk', help='Path to Pebble SDK (ie: ~/pebble-dev/PebbleSDK-2.X/)')
        if is_connect:
            parser.add_argument('host', type=str, nargs='?', default=libpebble.DEFAULT_WEBSOCKET_HOST, help='The host of the WebSocket server to connect')

    def sdk_path(self, args):
        """
        Tries to guess the location of the Pebble SDK
        """

        if args.sdk:
            return args.sdk
        else:
            return os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
