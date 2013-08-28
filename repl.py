#!/usr/bin/env python

import argparse
import logging
import pebble as libpebble
import code
import readline
import rlcompleter
import websocket
import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from autobahn.websocket import *
from pebble.EchoServerProtocol import *

def start_repl(pebble_id, lightblue, pair, ws, ws_ip="ws://localhost:9000"):
    pebble = libpebble.Pebble(pebble_id, using_lightblue=lightblue, pair_first=pair, using_ws=ws, ws_ip=ws_ip)
    readline.set_completer(rlcompleter.Completer(locals()).complete)
    readline.parse_and_bind('tab:complete')
    code.interact(local=locals())

logging.basicConfig(format='[%(levelname)-8s] %(message)s', level = logging.DEBUG)

parser = argparse.ArgumentParser(description='An interactive environment for libpebble.')
parser.add_argument('--pebble_id', metavar='PEBBLE_ID', type=str, help='the last 4 digits of the target Pebble\'s MAC address, or a complete MAC address')
parser.add_argument('--pair', action="store_true", help='pair to the pebble from LightBlue bluetooth API before connecting.')
parser.add_argument('--lightblue', action="store_true", help='use LightBlue bluetooth API')
parser.add_argument('--ws', action="store_true", help='use WebSockets API')
args = parser.parse_args()

if args.lightblue:
    start_repl(args.pebble_id, args.lightblue, args.pair, False)
else:
    echo_server_start(libpebble.DEFAULT_PEBBLE_PORT)
    start_repl(None, False, False, True)