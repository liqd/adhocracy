# -*- coding: utf-8 -*-
import copy
import base64

from adhocracy_kotti.testing import asset


image_file = asset("image_test.jpg")

image_data = base64.b64encode(image_file.read())


IMAGEDATA_APPSTRUCT = {"filename": u"test_image",
                       "mimetype": u"image/jpeg",
                       "tags": [u"tag1", u"tag2"],
                       "data": image_data,
                       }


def add_image(name, data):
    from kotti.resources import Image
    from adhocracy_kotti import utils
    images = utils.get_image_folder()
    images[name] = Image(**data)


def test_images_post_one(root, request):
    # root/request are pytest fixtures from kotti.test
    from adhocracy_kotti.mediacenter import images_post
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    request.validated = data
    result = images_post(request)
    name = u'urn-uuid-29cf7df1-b1f9-367e-b528'
    assert result == {'status': 'succeeded', 'name': name}
    assert root["mediacenter"][name].tags == [u'tag1', u'tag2']
    assert root["mediacenter"][name].size == 143124
    assert root["mediacenter"][name].title == u"test_image"


def test_images_post_multiple(root, request):
    import transaction
    from adhocracy_kotti.mediacenter import images_post
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    data["tags"] = [u"tag1", u"tag2"]
    request.validated = data
    result1 = images_post(request)
    data["tags"] = [u"tag1"]
    result2 = images_post(request)
    data["tags"] = []
    result3 = images_post(request)
    transaction.commit()
    name = u'urn-uuid-29cf7df1-b1f9-367e-b528'
    assert result1 == {'status': 'succeeded', 'name': name}
    assert result2 == {'status': 'succeeded', 'name': name}
    assert result3 == {'status': 'succeeded', 'name': name}


def test_images_get(root, request):
    #TODO Kotti is buggy, test multiple items with the same tag
    from adhocracy_kotti.mediacenter import images_get
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    data["size"] = 6
    data["tags"] = [u"tag1", u"tag2"]
    add_image("test_image", data)
    data["tags"] = [u"tag3"]
    add_image("test_image-1", data)
    data["tags"] = []
    add_image("test_image-2", data)

    request.validated = {"tags": []}
    result = images_get(request)
    assert len(result) == 3
    assert result[1] == {'filename': u'test_image',
                         'mimetype': u'image/jpeg',
                         'name': u'test_image-1',
                         'size': 6,
                         'tags': [u'tag3']}


def test_images_get_tags(root, dummy_request):
    from adhocracy_kotti.mediacenter import images_get
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    data["tags"] = [u"tag1", u"tag2"]
    add_image("test_image", data)
    data["tags"] = [u"tag3"]
    add_image("test_image-1", data)
    data["tags"] = []
    add_image("test_image-2", data)

    dummy_request.validated = {"tags": [u"tag2", u"tag1"]}
    result = images_get(dummy_request)
    assert len(result) == 1
    assert isinstance(result[0], dict)


def test_image_get(root, request):
    from adhocracy_kotti.mediacenter import image_get
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    add_image("test_image", data)
    request.validated = {"name": u"test_image"}
    request.subpath = u""
    response = image_get(request)
    assert response.content_type == "image/jpeg"


def test_image_delete(root, request):
    from adhocracy_kotti.mediacenter import image_delete
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    add_image("test_image", data)

    request.validated = {"name": u"test_image"}
    result = image_delete(request)
    assert root["mediacenter"].items() == []
    del result


def test_imagescale_get(root, request):
    from adhocracy_kotti.mediacenter import imagescale_get
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    data["data"] = base64.b64decode(data["data"])
    add_image("test_image", data)

    request.validated = {"name": u"test_image", "scale": "large"}
    response = imagescale_get(request)
    assert response.content_type == "image/jpeg"
