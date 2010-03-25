
import democracy
import text
import search
import event
import watchlist
import util
import queue

from version import get_version

from recommendations import recommend


def init_site():
    #util.replicate_fallback('static', 'img', 'header_logo.png')
    util.replicate_fallback('static', 'style', 'site.css')
    util.replicate_fallback('site.wsgi')
    #for page in ['index', 'about', 'imprint', 'privacy']:
    #    util.replicate_fallback('page', page + '.en.html')