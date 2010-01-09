"""
Versioning for the application, especially for the UI. 
"""

import re

svn_revision = "$Revision: 534 $"
svn_rev_re = re.compile("\$Revision: (\d*) \$")

rev_num = int(svn_rev_re.match(svn_revision).group(1))

REV_TEMPLATE = "2010.1 (r%s)"
# Modify this:
# foo schnasel // version bumping 

def get_version():
    """ Get a version identifier for use in the public user interface """
    return REV_TEMPLATE % rev_num