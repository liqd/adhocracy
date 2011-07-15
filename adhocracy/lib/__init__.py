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
    util.replicate_fallback('static', 'style', 'site.css')
    util.replicate_fallback('site.wsgi')
