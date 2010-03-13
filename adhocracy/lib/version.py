"""
Versioning for the application, especially for the UI. 
"""

import re

REV_TEMPLATE = "2010.2"
# Modify this:
# bar // version bumping 

def get_version():
    """ Get a version identifier for use in the public user interface """
    return REV_TEMPLATE