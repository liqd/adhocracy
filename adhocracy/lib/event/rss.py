from pylons import response, tmpl_context as c

from .. import helpers as h
from .. import pager
from .. import text
import formatting


from webhelpers.feedgenerator import RssUserland091Feed

def rss_feed(events, name, link, description):
        rss = RssUserland091Feed(name, link.encode('utf-8'), 
                                 description)
        def event_item(event):
            description = event.text()
            if description is None:
                description = unicode(u"%s %s" % (h.user_link(event.user), 
                                      formatting.as_html(event)))
            else: 
                description = text.render(description)
            item_link = link
            try:
                item_link = event.event.link_path(event)
            except:
                pass
            rss.add_item(title=u"%s %s" % (event.user.name, 
                         formatting.as_unicode(event)),
                         link=item_link.encode('utf-8'),
                         pubdate=event.time,
                         description=description,
                         author_name=event.user.name,
                         unique_id=unicode(event.id))
        
        response.content_type = 'application/rss+xml'
        pager.NamedPager('rss', events, event_item, size=50).here()
        return rss.writeString('utf-8')