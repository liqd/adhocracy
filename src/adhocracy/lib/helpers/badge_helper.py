from base64 import b64encode
import StringIO
from PIL import Image, ImageDraw


def generate_thumbnail_tag(badge, height="48", width="48"):
    """returns string with the badge thumbnail img tag
    """
    heigth = height
    width = width
    #TODO resize and get mimetype from PIL, joka
    #TODO cache, joka
    #TODO config option to set default width/height, joka
    mimetype = "image/png"
    img_template = """<img src="data:%s;base64,%s" height="%s" width="%s" />"""
    data = badge.thumbnail
    if not data:
        im = Image.new('RGB', (10, 10))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0,0,10,10), fill=badge.color, outline=badge.color)
        f = StringIO.StringIO()
        im.save(f, "PNG")
        data = f.getvalue()
        del draw, im, f
    data_enc = b64encode(data)
    return (img_template % (mimetype, data_enc, heigth, width))
