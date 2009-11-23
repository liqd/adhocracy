import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from adhocracy.lib.base import BaseController, render

log = logging.getLogger(__name__)

class TwitteroauthController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/twitteroauth.mako')
        # or, return a response
        return 'Hello World'
