import behavior
import democracy
import text
import search
import event
import watchlist
import util
import queue

from version import get_version

from recommendations import recommend


def init_site(app_conf):
    util.replicate_fallback('site.wsgi', app_conf=app_conf)
