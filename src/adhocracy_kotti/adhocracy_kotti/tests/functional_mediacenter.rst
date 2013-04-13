adhocracy medicenter REST-API browser tests
============================================

Setup
-----

    >>> from adhocracy_kotti.testing import setup_functional, asset
    >>> import json
    >>> import base64
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

    >>> resp = app.post_json("/images", image_data_post)
    >>> resp.status
    '200 OK'

The response body gives us the name to identifiy the image::

    >>> return_data = json.loads(resp.body)
    >>> name = return_data["name"]
    >>> name
    u'urn-uuid-f477dcfc-6da0-37d0-9f53'

Now we can get the image ::

    >>> resp = app.get("/images/%s" % str(name))
    >>> resp
    <200 OK image/jpeg body='\x...

or a specific image scale ::

    >>> app.get("/images/%s/large" % str(name))
    <200 OK image/jpeg body='\x...

We can also delete the image::

    >>> app.delete("/images/%s" % str(name))
    <200 OK application/json body='{"status...



