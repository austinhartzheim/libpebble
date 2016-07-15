__author__ = 'katharine'

import collections
import json
import logging
import os.path
import platform
import uuid

import requests

import PblAccount
import PblProject
from . import get_sdk_version


class PebbleAnalytics(object):
    TD_SERVER = ""

    def __init__(self):
        self.should_track = False

    @classmethod
    def _flatten(cls, d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = parent_key + '_0_' + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(cls._flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def submit_event(self, event, **data):
        return

    def _should_track(self):
        # Should we track analytics?
        return False

    def _get_persistent_dir(self):
        import LibPebblesCommand  # I hate libpebble.
        return LibPebblesCommand.LibPebbleCommand.get_persistent_dir()

    def _get_identity(self):
        return None

    def _get_machine_identifier(self):
        return None

    def _get_project_info(self):
        return None

    def _get_host_info(self):
        return None

    @classmethod
    def get_shared(cls, *args, **kwargs):
        return None

    @staticmethod
    def _is_running_in_vm():
        """ Return true if we are running in a VM """
        return False


# Convenience method.
def post_event(event, **data):
    return
