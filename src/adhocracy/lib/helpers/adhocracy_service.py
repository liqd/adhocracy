import base64
import json
import requests
import magic

from pylons import config


class RESTAPI(object):
    """Helper to work with the adhocarcy_service rest api
       (adhocracy_kotti.mediacenter, adhocracy_kotti.staticpages, plone).
    """

    session = requests.Session()

    #TODO make this a method
    images_get, images_post, images_delete = None, None, None
    """requests prepared requests to call /images"""

    def __init__(self):
        self.mediacenter_api_token = config.get(
            'adhocracy_service.mediacenter.rest_api_token',
            config.get('adhocracy_service.rest_api_token', ''))
        self.mediacenter_api_address = config.get(
            'adhocracy_service.mediacenter.rest_api_address',
            config.get('adhocracy_service.rest_api_address', ''))
        self.mediacenter_headers = {"X-API-Token": self.mediacenter_api_token}
        self.images_get = requests.Request(
            "GET",
            url=self.mediacenter_api_address + "images",
            headers=self.mediacenter_headers)
        self.images_post = requests.Request(
            "POST",
            url=self.mediacenter_api_address + "images",
            headers=self.mediacenter_headers)
        self.images_delete = requests.Request(
            "DELETE",
            url=self.mediacenter_api_address + "images",
            headers=self.mediacenter_headers)

    def add_image(self, filename, binarydata):
        """Post image data to the mediacenter

            returns requests response object
        """
        mimetype = magic.from_buffer(binarydata, mime=True)
        image_encoded = base64.b64encode(binarydata)
        request = self.images_post
        request.data = json.dumps(dict(filename=filename,
                                       data=image_encoded,
                                       mimetype=mimetype,
                                       ))
        return self.session.send(request.prepare())
