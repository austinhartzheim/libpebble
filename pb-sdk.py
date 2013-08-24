#!/usr/bin/python

import argparse

from pebble.PblCommand import PblCommand
from pebble.PblProjectCreator import PblProjectCreator
from pebble.PblBuildCommand import PblBuildCommand

class PbSDKShell:
  commands = []

  def __init__(self):
    self.commands.append(PblProjectCreator())
    self.commands.append(PblBuildCommand())

  def main(self):
    parser = argparse.ArgumentParser(description = 'Pebble SDK Shell')
    subparsers = parser.add_subparsers(dest="command", title="Command", description="Action to perform")
    for command in self.commands:
      subparser = subparsers.add_parser(command.name, help = command.help)
      command.configure_subparser(subparser)
    args = parser.parse_args()

    # Find the extension that was called
    command = [x for x in self.commands if x.name == args.command][0]
    command.run(args)

  def run_action(self, action):
    pass


if __name__ == '__main__':
  PbSDKShell().main()

