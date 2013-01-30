from base64 import b64encode
from hashlib import sha1
import StringIO
from PIL import Image, ImageDraw

from pylons import config
from pylons import tmpl_context as c

from adhocracy.lib import cache


def make_key(iden, args, kwargs):
    conf = config.get
    sig = iden[:200]\
        + cache.util.make_tag(conf("adhocracy.thumbnailbadges.width"))\
        + cache.util.make_tag(conf("adhocracy.thumbnailbadges.height"))\
        + cache.util.make_tag(c.instance.thumbnailbadges_width)\
        + cache.util.make_tag(c.instance.thumbnailbadges_height)\
        + cache.util.make_tag(args) \
        + cache.util.make_tag(kwargs)
    return sha1(sig).hexdigest()


@cache.memoize('badge_thumbnail', make_key=make_key)
def generate_thumbnail_tag(badge, width=0, height=0):
    """Returns string with the badge thumbnail img tag
       The image is resized and converted to PNG.
    """
    #TODO Generated image is not Working with IE < 8, joka

    size = (width and height) and (width, height)\
        or get_default_thumbnailsize(badge)
    img_template = """<img src="data:%s;base64,%s" height="%s" width="%s" />"""
    imagefile = StringIO.StringIO(badge.thumbnail)
    mimetype = "image/png"
    try:
        im = Image.open(imagefile)
        mimetype = "image/" + im.format.lower()
        im.thumbnail(size, Image.ANTIALIAS)
        f = StringIO.StringIO()
        im.save(f, 'PNG')
        del im, imagefile
        imagefile = f
    except IOError:
        colour = badge.color or u"#ffffff"
        im = Image.new('RGB', (10, 10))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0,0,10,10), fill=badge.color, outline=badge.color)
        f = StringIO.StringIO()
        im.save(f, "PNG")
        del draw, im
        imagefile = f
    data_enc = b64encode(imagefile.getvalue())
    del imagefile

    return (img_template % (mimetype, data_enc, str(size[1]), str(size[0])))


def get_default_thumbnailsize(badge):
    instance = badge.instance
    global_w = int(config.get("adhocracy.thumbnailbadges.width", "48"))
    global_h = int(config.get("adhocracy.thumbnailbadges.height", "48"))
    ins_w = instance and instance.thumbnailbadges_width
    ins_h = instance and instance.thumbnailbadges_height
    return (ins_w or global_w, ins_h or global_h)
