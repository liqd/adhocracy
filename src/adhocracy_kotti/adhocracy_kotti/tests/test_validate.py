# -*- coding: utf-8 -*-


def test_validate_image_data_valid(dummy_request):
    # dummy_request is a pytest fixture from conftest
    from adhocracy_kotti.validate import validate_image_data
    dummy_request.validated = {"data": b"binary_base64"}
    validate_image_data(dummy_request)
    assert(len(dummy_request.errors) == 0)


def test_validate_image_data_invalid(dummy_request):
    from adhocracy_kotti.validate import validate_image_data
    dummy_request.validated = {"data": u"wrong dötö"}
    validate_image_data(dummy_request)
    assert(len(dummy_request.errors) == 1)


def test_validate_api_token_valid(dummy_request):
    from adhocracy_kotti.validate import validate_api_token
    from adhocracy_kotti.testing import API_TOKEN
    dummy_request.headers["X-API-Token"] = API_TOKEN
    dummy_request.validated = {}
    validate_api_token(dummy_request)
    assert(len(dummy_request.errors) == 0)


def test_validate_api_token_invalid(dummy_request):
    from adhocracy_kotti.validate import validate_api_token
    dummy_request.headers["X-API-Token"] = "wrong token"
    dummy_request.validated = {}
    validate_api_token(dummy_request)
    assert(len(dummy_request.errors) == 1)


def test_validate_api_token_missing(dummy_request):
    from adhocracy_kotti.validate import validate_api_token
    dummy_request.validated = {}
    validate_api_token(dummy_request)
    assert(len(dummy_request.errors) == 1)


def test_validate_querystring_list_value_valid(dummy_request):
    pass
    #TODO


def test_validate_image_name_exists_valid(root, dummy_request):
    # root is a pytest fixture from kotti.tests
    from adhocracy_kotti.validate import validate_image_name_exists
    from adhocracy_kotti.utils import get_image_folder
    from kotti.resources import Image
    images = get_image_folder()
    images["exists"] = Image(title=u"exists")

    dummy_request.validated = {"name": "exists"}
    validate_image_name_exists(dummy_request)
    assert(len(dummy_request.errors) == 0)


def test_validate_image_name_exists_invalid(root, dummy_request):
    from adhocracy_kotti.validate import validate_image_name_exists
    dummy_request.validated = {"name": "notexists"}
    validate_image_name_exists(dummy_request)
    assert(len(dummy_request.errors) == 1)
