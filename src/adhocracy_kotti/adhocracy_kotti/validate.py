"""Rest web service validators"""
import base64
import binascii
import simplejson as json

from adhocracy_kotti import utils


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
    else:
        token = request.headers.get('X-API-Token', '')
        valid_token = request.registry.settings['rest_api_token']
        if token != valid_token:
            request.errors.add('header', 'X-API-Token',
                               'The token is invalid')


def validate_image_name_exists(request):
    image_name = request.validated["name"]
    images = utils.get_image_folder()
    if image_name not in images:
        request.errors.add('body', 'name', "This image name does not exists")
