from pylons import response, tmpl_context as c

from .. import helpers as h
from .. import templating
    

from webhelpers.feedgenerator import Rss201rev2Feed, RssUserland091Feed

def rss_feed(events, name, link, description):
        rss = Rss201rev2Feed(name, link, description)
        def event_item(event):
            rss.add_item(title="%s %s" % (event.agent.name, unicode(event)),
                         link=h.instance_url(c.instance),
                         pubdate=event.time,
                         description="%s %s" % (h.user_link(event.agent), 
                                                event.html()),
                         author_name=event.agent.name)
        response.content_type = 'application/rss+xml'
        templating.NamedPager('rss', events, event_item, count=100).here()
        return rss.writeString('utf-8')