"""
Versioning for the application, especially for the UI.
"""

from adhocracy import __version__


def get_version():
    """ Get a version identifier for use in the public user interface """
    return __version__
