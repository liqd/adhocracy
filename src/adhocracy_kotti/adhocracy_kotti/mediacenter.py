from kotti.resources import Image
from kotti.views.util import content_with_tags
from kotti.views.image import ImageView
from cornice import Service

from adhocracy_kotti import schemata
from adhocracy_kotti import utils


images = Service(name='images',
                 path='/images',
                 description="Service to get images or add new ones")


image = Service(name='image',
                path='/images/{name}/{scale}',
                description="Service to delete image or get image binary data")


#TODO use view classes instead of functions
@images.post(schema=schemata.ImagePOST, accept="text/json",)
def images_post(request):
    """Add new Image.

       mimetype value: "image/jpeg" | "image/png"
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


#@images.delete(accept="text/json")
#def images_delete(request):
    #"""Delete all Images

       #return codes: 200, 400, 500
    #"""
    #image_folder = utils.get_image_folder()
    #for k, i in image_folder.items():
        #if i.type == 'image':
            #del image_folder[k]
    #return {"status": "succeeded"}


@image.get(schema=schemata.ImageGETDATA, accept="text/json", renderer="binary")
def image_get(request):
    """Get one image binary

       returns: response
    """
    data = request.validated
    scale, name = data["scale"], data["name"]
    images = utils.get_image_folder()
    image = images[name]
    resp = ImageView(image, request).image(subpath="%s/download" % scale)
    return resp


# GET /images/id scale? linktype? :rtype: pyramid.response.Response
# DELETE /images/id rtype: {sucesses}
