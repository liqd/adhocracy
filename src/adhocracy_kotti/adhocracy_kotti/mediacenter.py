"""Medicenter rest web service"""
from kotti.resources import Image
from kotti.views.util import content_with_tags
from kotti.views.image import ImageView
from cornice import Service

from adhocracy_kotti import schemata
from adhocracy_kotti import utils
from adhocracy_kotti import validate


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


#TODO use view classes instead of functions
@images.post(schema=schemata.ImagePOST, accept="text/json",
             validators=(validate.validate_image_data,
                         validate.validate_api_token,))
def images_post(request):
    """Add new Image.

       mimetype value: "image/jpeg" | "image/png"
       data value: base64 encoded string
    """
    data = request.validated
    data["size"] = len(data["data"])
    image_folder = utils.get_image_folder()
    name = utils.generate_image_name(data["data"])
    if name not in image_folder:
        image_folder[name] = Image(**data)
    return {"name": name,
            "status": "succeeded"}


@images.get(schema=schemata.TagsList, accept="text/json",
            validators=(validate.validate_api_token,))
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


@image.delete(schema=schemata.ImageGETDATA, accept="text/json",
              validators=(validate.validate_api_token,))
def image_delete(request):
    """Delete the image
    """
    data = request.validated
    name = data["name"]
    images = utils.get_image_folder()
    del images[name]
    return {"status": "succeeded"}
