from datetime import datetime, timedelta

import formencode

from pylons import request, response, session, tmpl_context as c
from pylons.i18n import _, add_fallback, get_lang, set_lang, gettext
import webhelpers.date as date

import babel
from babel import Locale
import babel.dates 



LOCALES = [babel.Locale('en', 'US'), 
           babel.Locale('de', 'DE'),
           babel.Locale('fr', 'FR')]

DEFAULT = babel.Locale('en', 'US')

def handle_request():
    """
    Given a request, try to determine the appropriate locale to use for the 
    request. When a user is logged in, his or her settings will first be queried. 
    Otherwise, an appropriate locale will be negotiated between the browser 
    accept headers and the available locales.  
    """
    if c.user and c.user.locale:
        c.locale = c.user.locale
    else:
        lang = Locale.negotiate(request.languages, map(str, LOCALES)) \
                or str(DEFAULT)
        c.locale = Locale.parse(lang)
    
    # pylons 
    set_lang(c.locale.language)
    add_fallback(DEFAULT.language)
    formencode.api.set_stdtranslation(domain="FormEncode", languages=[c.locale.language])

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
    
def format_timedelta(td):    
    # version shit
    if hasattr(babel.dates, 'format_timedelta'):
        return babel.dates.format_timedelta(td, locale=c.locale.language)
    else:
        return date.time_ago_in_words(datetime.now() - td) 
    
def relative_time(dt):
    """ A short statement giving the time distance since ``dt``. """
    now = datetime.now()
    ago = now - dt
    if ago <= timedelta(days=2): 
        return _("%(ts)s ago") % {'ts': format_timedelta(dt - datetime.now())}
    else:
        return _("%(ts)s") % {'ts': babel.dates.format_date(dt, format='long', locale=c.locale)}
        