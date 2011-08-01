"""
Versioning for the application, especially for the UI.
"""

from pkg_resources import get_distribution


def get_version():
    """ Get a version identifier for use in the public user interface """
    return get_distribution("adhocracy").version
