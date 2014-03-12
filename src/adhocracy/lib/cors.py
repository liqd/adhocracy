class CorsMiddleware(object):
    """ Set CORS header.

    This middleware sets an Access-Control-Allow-Origin HTTP header allowing
    scripts from other domains to load Adhocracy data.

    In our case this is needed in the following case (non-relative URLs):

    - User visits foo.adhocracy.lan
    - Due to fanstatic loading everything from the main URL, a script is loaded
      from adhocracy.lan/js/myscript.js
    - This script wants to access JSON data from the same domain it comes from
      (js.socialshareprivacy-1.5 does that)
    - JSON from adhocracy.lan couldn't be loaded from foo.adhocracy.lan if
      the respective header weren't set.

    It would be sufficient to allow `*.adhocracy.lan` to access JSON data on
    `adhocracy.lan`, but the CORS specs don't allow for that. Therefore we
    allow everybody to use our data.

    """

    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        def local_response(status, headers, exc_info=None):
            headers.append(('Access-Control-Allow-Origin', '*'))
            start_response(status, headers, exc_info)
        return self.app(environ, local_response)
