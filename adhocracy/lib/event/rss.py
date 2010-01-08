from pylons import response, tmpl_context as c

from .. import helpers as h
from .. import templating
import formatting


from webhelpers.feedgenerator import RssUserland091Feed

def rss_feed(events, name, link, description):
        rss = RssUserland091Feed(name, link, description)
        def event_item(event):
            rss.add_item(title=u"%s %s" % (event.user.name, formatting.as_unicode(event)),
                         link=h.instance_url(event.instance, path=event.event.link_path(event)),
                         pubdate=event.time,
                         description=unicode(u"%s %s" % (h.user_link(event.user), 
                                                formatting.as_html(event))),
                         author_name=event.user.name,
                         unique_id=unicode(event.id))
        response.content_type = 'application/rss+xml'
        templating.NamedPager('rss', events, event_item, count=50).here()
        return rss.writeString('utf-8')