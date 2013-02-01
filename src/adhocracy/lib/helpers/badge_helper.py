from base64 import b64encode
from hashlib import sha1
import StringIO
from PIL import Image, ImageDraw

from pylons import config

from adhocracy.lib import cache


def make_key(iden, args, kwargs):
    conf = config.get
    instance = args[0].instance
    instance_w = instance and instance.thumbnailbadges_width or ""
    instance_h = instance and instance.thumbnailbadges_height or ""
    sig = iden[:200]\
        + cache.util.make_tag(conf("adhocracy.thumbnailbadges.width"))\
        + cache.util.make_tag(conf("adhocracy.thumbnailbadges.height"))\
        + cache.util.make_tag(instance_w + instance_h)\
        + cache.util.make_tag(args) \
        + cache.util.make_tag(kwargs)
    return sha1(sig).hexdigest()


@cache.memoize('badge_thumbnail', make_key=make_key)
def generate_thumbnail_tag(badge, width=0, height=0):
    """Returns string with the badge thumbnail img tag
       The image is resized and converted to PNG.
    """
    #NOTE Generated image is not Working with IE < 8, joka
    #TODO use real image links instead of URI:data

    size = (width and height) and (width, height)\
        or get_default_thumbnailsize(badge)
    img_template = """<img src="data:%s;base64,%s" height="%s" width="%s" />"""
    imagefile = StringIO.StringIO(badge.thumbnail)
    mimetype = "image/png"
    try:
        #resize image
        im = Image.open(imagefile)
        mimetype = "image/" + im.format.lower()
        im.thumbnail(size, Image.ANTIALIAS)
        #optimize image but preserve transparency
        im.load()
        im_opti = Image.new("RGB", im.size, (255, 255, 255))
        if len(im.split()) > 3:
            im_opti.paste(im, mask=im.split()[3])
        else:
            im_opti.paste(im)
        im_opti = im_opti.convert('P', colors=256, palette=Image.ADAPTIVE)
        #save image
        f = StringIO.StringIO()
        im_opti.save(f, 'PNG')
        del im, im_opti, imagefile
        imagefile = f
    except IOError:
        colour = badge.color or u"#ffffff"
        im = Image.new('RGB', (5, 5))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0, 0, 5, 5), fill=colour, outline=colour)
        im = im.convert('P', colors=1, palette=Image.ADAPTIVE)
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
