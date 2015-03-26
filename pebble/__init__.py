__title__ = 'libpebble'
__version__ = '0.0.1'
__build__ = 0x01
__license__ = 'MIT'


def get_sdk_version():
    try:
        from VersionGenerated import SDK_VERSION
        return SDK_VERSION
    except ImportError:
        return "unknown-version"
