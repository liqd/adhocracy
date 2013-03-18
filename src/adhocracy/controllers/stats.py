from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_json


class StatsController(BaseController):
    """ This controller is an endpoint for AJAX requests that monitor user
    behavior. You'll want to enable `adhocracy.requestlog_active` to record
    them.  """
    def read_comments(self, format='json'):
        return render_json({})
