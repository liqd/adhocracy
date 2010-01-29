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

@memoize('instance_image')
def load(instance, size, fallback=DEFAULT):
    instance_path = _instance_logo_path(instance)
    if not os.path.exists(instance_path):
        instance_path = util.get_path(*fallback)
    logo_image = Image.open(instance_path)
    logo_image.thumbnail(size, Image.ANTIALIAS)
    sio = StringIO.StringIO()
    logo_image.save(sio, 'PNG')
    return (instance_path, sio.getvalue())

def load_header(instance):
    global header_image
    if header_image is None:
        header_image = Image.open(util.get_path(*HEADER))
    return load(instance, header_image.size, fallback=HEADER)
    
    