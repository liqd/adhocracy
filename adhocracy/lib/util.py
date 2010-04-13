import uuid
import logging
import os
import os.path
import shutil

from pylons import config
from pylons.controllers.util import abort
from pylons.i18n import _

log = logging.getLogger(__name__)

def timedelta2seconds(delta):
    """ Convert a given timedelta to a number of seconds """
    return delta.microseconds / 1000000.0 \
           + delta.seconds + delta.days * 60*60*24 
           
def random_token():
    """ Get a random string, the first char group of a uuid4 """
    return unicode(uuid.uuid4()).split('-').pop()

def get_entity_or_abort(cls, id, instance_filter=True, **kwargs):
    from templating import ret_abort
    """ 
    Return either the instance identified by the given ID or
    raise a HTTP 404 Exception within the controller. 
    """ 
    if not hasattr(cls, 'find'):
        raise TypeError("The given class does not have a find() method")
    obj = cls.find(id, instance_filter=instance_filter, **kwargs)
    if not obj:
        ret_abort(_("Could not find the entity '%s'") % id, code=404)
    return obj


# File system related functions:

def get_site_directory():
    rel = config.get('adhocracy.site.dir', 
                     os.path.join(config.get('here'), 'site'))
    site_directory = os.path.abspath(rel)
    if not os.path.exists(site_directory):
        os.makedirs(site_directory)
    elif not os.path.isdir(site_directory):
        raise IOError("adhocracy.site.dir must be a directory!")
    return site_directory

def get_fallback_directory():
    from pprint import pprint
    return os.path.abspath(config.get('pylons.paths').get('root')) 

def compose_path(basedir, *a):
    path = os.path.join(basedir, *a)
    path = os.path.abspath(path)
    if not path.startswith(basedir):
        # escape attempt
        raise IOError("Path outside scope")
    return path     

def get_site_path(*a):
    return compose_path(get_site_directory(), *a)

def get_path(*a):
    path = compose_path(get_site_directory(), *a)
    if not os.path.exists(path):
        path = compose_path(get_fallback_directory(), *a)
    if not os.path.exists(path):
        return None
    return path

def create_site_subdirectory(*a):
    path = get_site_path(*a)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def replicate_fallback(*a):
    to_path = get_site_path(*a)
    if not os.path.exists(to_path):
        log.debug("Setting up site item at: %s" % to_path)
        to_dir = os.path.dirname(to_path)
        if not os.path.exists(to_dir):
            os.makedirs(to_dir)
        from_path = get_path(*a)
        if from_path is None:
            raise IOError("Site file does not exist.")
        if not from_path == to_path:
            shutil.copy(from_path, to_path)
    return to_path

