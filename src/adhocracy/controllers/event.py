import logging

from pylons import request, tmpl_context as c
from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import event, helpers as h
from adhocracy.lib import pager
from adhocracy.lib.auth import guard
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_def

log = logging.getLogger(__name__)


class EventController(BaseController):

    identifier = 'events'

    @guard.perm('event.index_all')
    def all(self, format='html'):
        query = model.Event.all_q(include_hidden=False)\
            .order_by(model.Event.time.desc())\

        if 'event_filter' in request.params:
            query = query.filter(model.Event.event.in_(
                request.params.getall('event_filter')))

        query = query.limit(min(int(request.params.get('count', 50)), 100))
        events = query.all()

        if format == 'rss':
            return event.rss_feed(events,
                                  _('%s News' % h.site.name()),
                                  h.base_url(instance=None),
                                  _("News from %s") % h.site.name())

        elif format == 'ajax':
            return render_def('/event/tiles.html', 'carousel',
                              events=events)
        else:
            c.event_pager = pager.events(events, count=50)

            if format == 'overlay':
                return render('/event/all.html', overlay=True)
            else:
                return render('/event/all.html')
