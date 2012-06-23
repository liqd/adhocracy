import os.path
import logging
import StringIO

try:
    import Image
except ImportError:
    from PIL import Image


from cache import memoize
import util

log = logging.getLogger(__name__)

HEADER = ['static', 'img', 'header_logo.png']
DEFAULT = ['static', 'img', 'icons', 'site_64.png']

header_image = None


def _instance_logo_path(key):
    util.create_site_subdirectory('uploads', 'instance')
    return util.get_site_path('uploads', 'instance', key + '.png')


def store(instance, file):
    logo_image = Image.open(file)
    logo_image.save(_instance_logo_path(instance.key))


def delete(instance):
    if exists(instance.key):
        path = _instance_logo_path(instance.key)
        os.remove(path)


def exists(key):
    instance_path = _instance_logo_path(key)
    return os.path.exists(instance_path)


@memoize('instance_image', 3600)
def load(key, size, fallback=DEFAULT):
    x, y = size
    instance_path = _instance_logo_path(key)
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
