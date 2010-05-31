from datetime import datetime, timedelta

import formencode

from pylons import request, response, session, tmpl_context as c, config
from pylons.i18n import _, add_fallback, get_lang, set_lang, gettext
import webhelpers.date as date

import babel
from babel import Locale
import babel.dates 
from babel.dates import format_time
from extra_strings import *


LOCALES = [babel.Locale('en', 'US'), 
           babel.Locale('de', 'DE'),
           babel.Locale('fr', 'FR')]

def get_default_locale():
    if c.instance and c.instance.locale:
        return c.instance.locale
    locale = config.get('adhocracy.language', 'en_US')
    return babel.Locale.parse(locale)

def handle_request():
    """
    Given a request, try to determine the appropriate locale to use for the 
    request. When a user is logged in, his or her settings will first be queried. 
    Otherwise, an appropriate locale will be negotiated between the browser 
    accept headers and the available locales.  
    """
    c.locale = user_language(c.user, request.languages)


def user_language(user, fallbacks=[]):
    locale = None
    if user and user.locale:
        locale = user.locale
    else:
        locales = map(str, LOCALES)
        #print locales
        locale = Locale.parse(Locale.negotiate(fallbacks, locales)) \
                 or get_default_locale()
        #print "LANG", lang
    
    # pylons 
    set_lang(locale.language)
    add_fallback(get_default_locale().language)
    formencode.api.set_stdtranslation(domain="FormEncode", languages=[locale.language])
    return locale


def relative_date(time):
    """ Date only, not date & time. """
    date = time.date()
    today = date.today()
    if date == today:
        return _("Today")
    elif date == (today - timedelta(days=1)):
        return _("Yesterday")
    else:
        return dates.format_date(date, 'long', c.locale)

  
def countdown_time(dt, default):
    # THIS IS A HACK TO GET RID OF BABEL 
    if dt is not None:
        delta = dt - datetime.utcnow()
        default = delta.days
    return _("%d days") % default


def format_date(dt):
    ts = babel.dates.format_date(dt, format='long', locale=c.locale)
    return _("%(ts)s") % {'ts': ts}


def relative_time(dt):
    """ A short statement giving the time distance since ``dt``. """
    fmt = "<abbr class='timeago' title='%(iso)sZ'>%(formatted)s</abbr>"
    return fmt % dict(iso=dt.isoformat(), 
                      formatted=format_date(dt))

