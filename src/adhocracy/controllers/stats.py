from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render_json

class StatsController(BaseController):

    def read_comments(self, format='json'):
        return render_json({})
