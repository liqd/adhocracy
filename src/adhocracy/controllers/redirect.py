from pylons.controllers.util import redirect
from adhocracy.lib.base import BaseController
from adhocracy.lib.outgoing_link import decode_redirect


class RedirectController(BaseController):

    def outgoing_link(self, url_enc):
        url = decode_redirect(url_enc.decode('ascii'))
        return redirect(url)
