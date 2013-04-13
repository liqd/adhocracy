def test_validate_image_data_valid(dummy_request):
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
