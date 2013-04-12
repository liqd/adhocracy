import base64
import binascii
from kotti.resources import Image
from kotti.views.util import content_with_tags
from kotti.views.image import ImageView
from cornice import Service

from adhocracy_kotti import schemata
from adhocracy_kotti import utils


images = Service(
    name='images',
    path='/images',
    description="Service to get images or add new ones")

image = Service(
    name='image',
    path='/images/{name}',
    description="Service to delete image or get the image binary data")

imagescale = Service(
    name='imagescale',
    path='/images/{name}/{scale}',
    description="Service to get a scaled image binary data")


def validate_image_data(request):
    data_raw = request.validated.get("data", b"")
    try:
        data = base64.decodestring(data_raw)
        request.validated["data"] = data
    except (binascii.Error, UnicodeEncodeError) as e:
        error = u"The image data is not valid base64 encoding: %s"
        request.errors.add('body', 'data', error % e)


#TODO use view classes instead of functions
@images.post(schema=schemata.ImagePOST, accept="text/json",
             validators=(validate_image_data,))
def images_post(request):
    """Add new Image.

       mimetype value: "image/jpeg" | "image/png"
       data value: base64 encoded string
    """
    data = request.validated
    data["size"] = len(data["data"])
    image_folder = utils.get_image_folder()
    name = utils.find_name(image_folder, data["filename"])
    image_folder[name] = Image(**data)
    return {"name": name,
            "status": "succeeded"}


@images.get(schema=schemata.TagsList, accept="text/json")
def images_get(request):
    """Get all Images

       returns: Sequence of ImageGET
    """
    tags = request.validated["tags"]
    images = []
    if not tags:
        image_folder = utils.get_image_folder()
        images = [i for i in image_folder.values() if i.type == 'image']
    else:
        images = [i for i in content_with_tags(tags) if i.type == 'image']
    imagesdata = [utils.to_appstruct(i, schemata.ImageGET()) for i in images]
    return imagesdata


@imagescale.get(schema=schemata.ImageGETDATA, accept="text/json",)
def imagescale_get(request):
    """Get the image binary with specific scale

       returns: response
    """
    data = request.validated
    scale, name = data["scale"], data["name"]
    images = utils.get_image_folder()
    image = images[name]
    resp = ImageView(image, request).image(subpath="%s/download" % scale)
    return resp


@image.get(schema=schemata.ImageGETDATA, accept="text/json",)
def image_get(request):
    """Get the image binary

       returns: response
    """
    data = request.validated
    name = data["name"]
    images = utils.get_image_folder()
    image = images[name]
    resp = ImageView(image, request).image(subpath="%s/download" % scale)
    return resp


@image.delete(schema=schemata.ImageGETDATA, accept="text/json")
def image_delete(request):
    """Delete the image
    """
    data = request.validated
    name = data["name"]
    images = utils.get_image_folder()
    del images[name]
    return {"status": "succeeded"}
