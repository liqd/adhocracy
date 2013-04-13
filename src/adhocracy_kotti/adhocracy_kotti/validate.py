"""Rest web service validators"""
import base64
import binascii


def validate_image_data(request):
    data_raw = request.validated.get("data", b"")
    try:
        data = base64.decodestring(data_raw)
        request.validated["data"] = data
    except (binascii.Error, UnicodeEncodeError) as e:
        error = u"The image data is not valid base64 encoding: %s"
        request.errors.add('body', 'data', error % e)


def validate_api_token(request):
    if not 'X-API-Token' in request.headers:
        request.errors.add('header', 'X-API-Token',
                           'You need to provied a valid token')
    token = request.headers.get('X-API-Token', '')
    valid_token = request.registry.settings['rest_api_token']
    if token != valid_token:
        request.errors.add('header', 'X-API-Token',
                           'The token is invalid')
