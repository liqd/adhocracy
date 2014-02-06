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


"""This provides a simple api for adding logos to entities."""


FALLBACK = ['static', 'images', 'fallback.png']
INSTANCE = ['static', 'img', 'icons', 'site_64.png']
USER = ['static', 'img', 'icons', 'user.png']

ALLOWED_SIZES = [
    (32, 32), (None, 32),
    (48, 48), (None, 48),
    (64, 64), (None, 64),
    (256, 256), (None, 256),
    (256, 128),
    (960, 213),
]


class NoSuchSizeError(Exception):
    pass


def _entity_key(entity):
    if hasattr(entity, u'key'):
        return entity.key
    else:
        return u"%s-%i" % (entity.__class__.__name__, entity.id)


def validate_xy(x, y, y_default=24):
    try:
        y = int(y)
    except ValueError, ve:
        log.debug(ve)
        y = y_default
    try:
        x = int(x)
    except:
        x = None
    return x, y


def _logo_path(key):
    """the folder is called "instance" for backwards compability"""
    util.create_site_subdirectory('uploads', 'instance')
    return util.get_site_path('uploads', 'instance', key + '.png')


def store(entity, file):
    logo_image = Image.open(file)
    key = _entity_key(entity)
    logo_image.save(_logo_path(key))


def delete(entity):
    if exists(entity):
        key = _entity_key(entity)
        path = _logo_path(key)
        os.remove(path)
        return True


def exists(entity):
    key = _entity_key(entity)
    entity_path = _logo_path(key)
    return os.path.exists(entity_path)


def path_and_mtime(entity, fallback=None):
    """
    Return a tuple with the path to the entity's logo and
    the mtime (converted to an int).

    *entity*
        Get path and mtime for this entity
    *fallback* (tuple of str)
        A fallback path tuple to a logo if the entity
        doesn't have one.

    Returns:
       a (path (`str`), mtime (`int`)) tuple.
    """
    if fallback is None:
        fallback = FALLBACK
    key = _entity_key(entity)
    logo_path = _logo_path(key)
    if not os.path.exists(logo_path):
        logo_path = util.get_path(*fallback)
    mtime = os.path.getmtime(logo_path)
    # strip the fraction to get full seconds
    mtime = int(mtime)
    return logo_path, mtime


def load(entity, size, fallback=None):
    '''
    Load an entity logo or the fallback logo in a
    certain size.

    *entity*
         Get logo for this entity
    *size* (two-tuple of int)
         A tuple with the size like (x_size, y_size) where
         both are int values. x_size may be None in which case
         the image will be scaled down to y_size preserving
         the aspect ratio.

    Returns:
         A tuple with (image_path, mtime, image_data)
         Where image_path is the path on the file system,
         mtime is the mtime of the image file, and image_data
         is a string containing the image data.
    '''
    logo_path, mtime = path_and_mtime(entity, fallback)
    image_data = _load_with_mtime(logo_path, mtime, size)
    return (logo_path, mtime, image_data)


@memoize('instance_image', 3600 * 24)
def _load_with_mtime(logo_path, mtime, size):
    """
    Function to load the logo with sane caching.  The *mtime*
    parameter is the mtime of the current logo file. If the file
    changes it's mtime changes and we don't get outdated cache
    results anymore.

    *logo_path* (string)
         The path to the image file
    *mtime*
         The mtime of the image file or another unique identifier.
         This is used only to modify the cache key if the function
         is cached.
    *size* (two-tuple of int)
         A tuple with the size like (x_size, y_size) where
         both are int values. x_size may be None in which case
         the image will be scaled down to y_size preserving
         the aspect ratio. If x_size is not None the image may get
         cropped.

    Returns:
         A string containing the resized image data.
    """
    if size not in ALLOWED_SIZES:
        raise NoSuchSizeError()
    w, h = size
    logo_image = Image.open(logo_path)
    orig_w, orig_h = logo_image.size

    if w is None:
        # aspect ratio stays the same
        w = h * orig_w / orig_h
        logo_image.thumbnail((w, h), Image.ANTIALIAS)
    else:
        # The image is resized to be at least the requested size while
        # preserving the aspect ratio. Then it is cropped to the requested
        # size.
        if w * orig_h > h * orig_w:
            old_h = h * orig_w / w
            x0 = 0
            x1 = orig_w
            y0 = (orig_h - old_h) / 2
            y1 = y0 + old_h
        else:
            old_w = w * orig_h / h
            x0 = (orig_w - old_w) / 2
            x1 = x0 + old_w
            y0 = 0
            y1 = orig_h
        logo_image = logo_image.transform((w, h), Image.EXTENT,
                                          (x0, y0, x1, y1), Image.BICUBIC)

    sio = StringIO.StringIO()
    logo_image.save(sio, 'PNG')
    return sio.getvalue()
