import logging

from pylons import request, tmpl_context as c
from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import event, helpers as h
from adhocracy.lib import pager
from adhocracy.lib.auth import require
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, render_def
from adhocracy.lib.templating import OVERLAY_SMALL

log = logging.getLogger(__name__)


class EventController(BaseController):

    identifier = 'events'

    def all(self, format='html'):
        if c.instance is None:
            require.perm('event.index_all')

        events = model.Event.all_q(
            instance=c.instance,
            include_hidden=False,
            event_filter=request.params.getall('event_filter'))\
            .order_by(model.Event.time.desc())\
            .limit(min(int(request.params.get('count', 50)), 100)).all()

        if format == 'rss':
            return event.rss_feed(events,
                                  _('%s News' % h.site.name()),
                                  h.base_url(instance=None),
                                  _("News from %s") % h.site.name())

        elif format == 'ajax':
            query_params = request.params.copy()
            while True:
                try:
                    query_params.pop('count')
                except KeyError:
                    break

            more_url = h.base_url(instance=c.instance,
                                  member='event/all',
                                  query_params=query_params)
            return render_def('/event/tiles.html', 'carousel',
                              events=events, more_url=more_url)
        else:
            c.event_pager = pager.events(events, count=50)

            if format == 'overlay':
                return render('/event/all.html', overlay=True,
                              overlay_size=OVERLAY_SMALL)
            else:
                return render('/event/all.html')

    def carousel(self, format=u'html'):
        if c.instance is None:
            require.perm('event.index_all')

        data = {
            u'data_url': h.base_url('/event/all', query_params=request.params)
        }

        return render('/event/carousel.html', data,
                      overlay=format == u'overlay',
                      overlay_size=OVERLAY_SMALL)
