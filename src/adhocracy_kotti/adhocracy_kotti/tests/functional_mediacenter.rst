adhocracy medicenter REST-API browser tests
============================================

Setup
-----

    >>> import base64
    >>> import copy
    >>> import json
    >>> import pytest
    >>> from webtest import AppError
    >>> from adhocracy_kotti.testing import setup_functional, asset, API_TOKEN

    >>> tools = setup_functional()
    >>> app = tools["test_app"]

    >>> image_file = asset("image_test.jpg")
    >>> image_data = base64.b64encode(image_file.read())
    >>> image_data_post = {'data': image_data,
    ...     'filename': u'test_image',
    ...     'mimetype': u'image/jpeg',
    ...     'tags': [u'tag1', u'tag2']}


Add image and get image scale
-----------------------------

We can add a new image to the medicenter::

    >>> resp = app.post_json("/images", image_data_post, headers=[('X-API-Token', API_TOKEN)])
    >>> resp.status
    '200 OK'

The response body gives us the name to identifiy the image::

    >>> return_data = json.loads(resp.body)
    >>> name = return_data["name"]
    >>> name
    u'urn-uuid-f477dcfc-6da0-37d0-9f53'

Now we can get the image ::

    >>> resp = app.get("/images/%s" % str(name), headers=[('X-API-Token', API_TOKEN)])
    >>> resp
    <200 OK image/jpeg body='\x...

or a specific image scale ::

    >>> app.get("/images/%s/large" % str(name), headers=[('X-API-Token', API_TOKEN)])
    <200 OK image/jpeg body='\x...

We can also delete the image::

    >>> app.delete("/images/%s" % str(name), u"", headers=[('X-API-Token', API_TOKEN)])
    <200 OK application/json body='{"status...

If we send invalid data we get a nice error description::

    >>> import copy
    >>> image_data_invalid = copy.deepcopy(image_data_post)
    >>> del image_data_invalid["data"]
    >>> with pytest.raises(AppError) as err:
    ...     resp = app.post_json("/images", image_data_invalid, headers=[('X-API-Token', API_TOKEN)])
    >>> err.value.args[0].splitlines()[0] # doctest: +ELLIPSIS
    u'Bad response: 400 ...
    >>> err.value.args[0].splitlines()[1]
    u'{"status": "error", "errors": [{"location": "body", "name": "data", "description": "data is missing"}]}'
