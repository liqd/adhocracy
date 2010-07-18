from pylons import response, tmpl_context as c

from .. import helpers as h
from .. import pager
import formatting


from webhelpers.feedgenerator import Rss201rev2Feed as Feed

def rss_feed(events, name, link, description):
        rss = Feed(name, link.encode('utf-8'), 
                                 description)
        def event_item(event):
            try:
                item_link = event.event.link_path(event)
            except:
                item_link = link
            
            rss.add_item(title=u"%s %s" % (event.user.name, 
                         formatting.as_unicode(event)),
                         link=item_link.encode('utf-8'),
                         pubdate=event.time,
                         description=event.text(),
                         author_name=event.user.name,
                         unique_id=unicode(event.id))
        
        response.content_type = 'application/rss+xml'
        pager.NamedPager('rss', events, event_item, size=50).here()
        return rss.writeString('utf-8')