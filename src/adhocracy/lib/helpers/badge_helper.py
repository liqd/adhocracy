from base64 import b64encode
import StringIO
from PIL import Image, ImageDraw

from pylons import config


def generate_thumbnail_tag(badge, width="", height=""):
    """returns string with the badge thumbnail img tag
    """
    #TODO cache, joka
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
    except IOError:
        colour = badge.color or u"#ffffff"
        im = Image.new('RGB', (10, 10))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0,0,10,10), fill=badge.color, outline=badge.color)
        f = StringIO.StringIO()
        im.save(f, "PNG")
        imagefile = f
        del draw, im
    data_enc = b64encode(imagefile.getvalue())
    del imagefile

    return (img_template % (mimetype, data_enc, size[1], size[0]))


def get_default_thumbnailsize(badge):
    instance = badge.instance
    global_w = config.get("adhocracy.thumbnailbadges.width", "48")
    global_h = config.get("adhocracy.thumbnailbadges.height", "48")
    ins_w = instance and str(instance.thumbnailbadges_width)
    ins_h = instance and str(instance.thumbnailbadges_height)
    return (ins_w or global_w, ins_h or global_h)
