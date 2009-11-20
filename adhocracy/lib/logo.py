import os.path
import logging
import StringIO

import Image

from pylons import config 

from cache import memoize

log = logging.getLogger(__name__)
    
HEADER = os.path.join(config['pylons.paths']['static_files'], 
                             'img', 'header_logo.png')
DEFAULT = os.path.join(config['pylons.paths']['static_files'], 
                              'img', 'icons', 'bonsai_64.png')
PATH = os.path.join(config['cache.dir'], 'img', '%(key)s.png')    

def store(instance, file):
    try:
        logo_image = Image.open(file)
        logo_image.save(PATH % {'key': instance.key})
    except Exception, e:
        log.debug(e)
        return None

@memoize('instance_image')
def load(instance, size=None, header=False):
    logo_image = None
    header_image = None
    if header:
        header_image = Image.open(HEADER)
    instance_path = PATH % {'key': instance.key if instance else '--'}
    if os.path.exists(instance_path):
        logo_image = Image.open(instance_path)
    else:
        logo_image = header_image if header else Image.open(DEFAULT)
    if not size:
        size = header_image.size 
    logo_image.thumbnail(size, Image.ANTIALIAS)
    sio = StringIO.StringIO()
    logo_image.save(sio, 'PNG')
    return sio.getvalue()
    