#!/usr/bin/env python

import argparse
import pebble as libpebble
import code
import readline
import rlcompleter

def start_repl(pebble_id, lightblue, pair, ws, ws_ip):
    pebble = libpebble.Pebble(pebble_id, using_lightblue=lightblue, pair_first=pair, using_ws=ws, ws_ip=ws_ip)
    readline.set_completer(rlcompleter.Completer(locals()).complete)
    readline.parse_and_bind('tab:complete')
    code.interact(local=locals())

parser = argparse.ArgumentParser(description='An interactive environment for libpebble.')
parser.add_argument('pebble_id', metavar='PEBBLE_ID', type=str, help='the last 4 digits of the target Pebble\'s MAC address, or a complete MAC address')
parser.add_argument('--pair', action="store_true", help='pair to the pebble from LightBlue bluetooth API before connecting.')
parser.add_argument('--lightblue', action="store_true", help='use LightBlue bluetooth API')
parser.add_argument('--ws', action="store_true", help='use WebSockets API')
parser.add_argument('ws_ip', metavar='WS_IP', nargs='?', type=str, help='WS address of websocket server')
args = parser.parse_args()

if args.ws:
    start_repl(None, args.lightblue, args.pair, args.ws, args.ws_ip)
if args.lightblue:
    start_repl(args.pebble_id, args.lightblue, args.pair, args.ws, args.ws_ip)
else:
    start_repl(args.pebble_id, args.lightblue, args.pair, args.ws)