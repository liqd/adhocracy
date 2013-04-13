# -*- coding: utf-8 -*-
import copy
import base64
import pytest
from webtest import AppError

from adhocracy_kotti.testing import asset


image_file = asset("image_test.jpg")

image_data = base64.b64encode(image_file.read())


IMAGEDATA_APPSTRUCT = {"filename": u"test_image",
                       "mimetype": u"image/jpeg",
                       "tags": [u"tag1", u"tag2"],
                       "data": b"image_data",
                       }


def test_validate_image_data_valid(dummy_request):
    from adhocracy_kotti.mediacenter import validate_image_data
    dummy_request.validated = {"data": b"binary_base64"}
    validate_image_data(dummy_request)
    assert(len(dummy_request.errors) == 0)


def test_validate_image_data_invalid(dummy_request):
    from adhocracy_kotti.mediacenter import validate_image_data
    dummy_request.validated = {"data": u"wrong dötö"}
    validate_image_data(dummy_request)
    assert(len(dummy_request.errors) == 1)


def test_images_post_one(root, request):  # pytest public fixtures: conftest.py
    from adhocracy_kotti.mediacenter import images_post
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    request.validated = data
    result = images_post(request)
    name = u'urn-uuid-2be14549-b985-3aaf-ad9f'
    assert result == {'status': 'succeeded', 'name': name}
    assert root["mediacenter"][name].tags == [u'tag1', u'tag2']
    assert root["mediacenter"][name].size == 10


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
    name = u'urn-uuid-2be14549-b985-3aaf-ad9f'
    assert result1 == {'status': 'succeeded', 'name': name}
    assert result2 == {'status': 'succeeded', 'name': name}
    assert result3 == {'status': 'succeeded', 'name': name}


def test_images_post_functional_invalid_missing_fields(testapp, root):
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    del data["data"]
    with pytest.raises(AppError) as err:
        testapp.post_json("/images", data)
    assert err.value.args[0].splitlines()[1] ==\
        u'{"status": "error", "errors": '\
        u'[{"location": "body", '\
        u'"name": "data", "description": "data is missing"}]}'
    assert err.value.args[0].splitlines()[0].startswith(
        u'Bad response: 400')


def test_images_get(root, request):
    #TODO Kotti is buggy, test multiple items with the same tag
    from kotti.resources import Image
    from adhocracy_kotti import utils
    from adhocracy_kotti.mediacenter import images_get
    images = utils.get_image_folder()
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    data["size"] = 6
    data["tags"] = [u"tag1", u"tag2"]
    images["test_image"] = Image(**data)
    data["tags"] = [u"tag3"]
    images["test_image-1"] = Image(**data)
    data["tags"] = []
    images["test_image-2"] = Image(**data)

    request.validated = {"tags": []}
    result = images_get(request)
    assert len(result) == 3
    assert result[1] == {'filename': u'test_image',
                         'mimetype': u'image/jpeg',
                         'name': u'test_image-1',
                         'size': 6,
                         'tags': [u'tag3']}


def test_images_get_tags(root, dummy_request):
    #TODO more more DRY
    from kotti.resources import Image
    from adhocracy_kotti.mediacenter import images_get
    images = root["mediacenter"] = Image(title="mediacenter")
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    data["tags"] = [u"tag1", u"tag2"]
    images["test_image"] = Image(**data)
    data["tags"] = [u"tag3"]
    images["test_image-1"] = Image(**data)
    data["tags"] = []
    images["test_image-2"] = Image(**data)

    dummy_request.validated = {"tags": [u"tag2", u"tag1"]}
    result = images_get(dummy_request)
    assert len(result) == 1
    assert isinstance(result[0], dict)


def test_image_get(root, request):
    from kotti.resources import Image
    from adhocracy_kotti import utils
    from adhocracy_kotti.mediacenter import image_get
    images = utils.get_image_folder()
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    images["test_image"] = Image(**data)

    request.validated = {"name": u"test_image"}
    request.subpath = u""
    response = image_get(request)
    assert response.content_type == "image/jpeg"


def test_image_delete(root, request):
    from kotti.resources import Image
    from adhocracy_kotti import utils
    from adhocracy_kotti.mediacenter import image_delete
    images = utils.get_image_folder()
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    images["test_image"] = Image(**data)

    request.validated = {"name": u"test_image"}
    result = image_delete(request)
    assert images.items() == []
    del result


def test_imagescale_get(root, request):
    from kotti.resources import Image
    from adhocracy_kotti import utils
    from adhocracy_kotti.mediacenter import imagescale_get
    images = utils.get_image_folder()
    data = copy.deepcopy(IMAGEDATA_APPSTRUCT)
    images["test_image"] = Image(**data)

    request.validated = {"name": u"test_image", "scale": "large"}
    response = imagescale_get(request)
    assert response.content_type == "image/jpeg"
