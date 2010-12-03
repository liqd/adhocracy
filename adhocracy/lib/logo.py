import os.path
import logging
import StringIO

import Image

from pylons import config 

from cache import memoize
import util

log = logging.getLogger(__name__)
    
HEADER = ['static', 'img', 'header_logo.png']
DEFAULT = ['static', 'img', 'icons', 'site_64.png']

header_image = None

def _instance_logo_path(instance):
    util.create_site_subdirectory('uploads', 'instance')
    key = instance.key if instance else '-#-'
    return util.get_site_path('uploads', 'instance', key + '.png')


def store(instance, file):
    logo_image = Image.open(file)
    logo_image.save(_instance_logo_path(instance))


@memoize('instance_image', 3600)
def load(instance, size, fallback=DEFAULT):
    x, y = size
    instance_path = _instance_logo_path(instance)
    if not os.path.exists(instance_path):
        instance_path = util.get_path(*fallback)
    logo_image = Image.open(instance_path)
    if x is None: 
        orig_x, orig_y = logo_image.size
        x = int(y * (float(orig_x) / float(orig_y)))
    logo_image.thumbnail((x, y), Image.ANTIALIAS)
    sio = StringIO.StringIO()
    logo_image.save(sio, 'PNG')
    return (instance_path, sio.getvalue())


    
    