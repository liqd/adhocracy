import logging

from pylons import tmpl_context as c

from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy import model
from adhocracy.lib import tiles
from adhocracy.lib.auth.authorization import has_permission
from adhocracy.lib.base import BaseController
from adhocracy.lib.pager import NamedPager
from adhocracy.lib.templating import render

log = logging.getLogger(__name__)


class EventController(BaseController):

    @ActionProtector(has_permission("global.admin"))
    def all(self):
        query = model.meta.Session.query(model.Event)
        query = query.order_by(model.Event.time.desc())
        query = query.limit(200)
        c.event_pager = NamedPager('events', query.all(),
                                   tiles.event.row, count=50)
        return render('/event/all.html')
