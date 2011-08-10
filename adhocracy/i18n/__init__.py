from datetime import datetime, timedelta
import pkgutil

import formencode

from pylons import config
from pylons.i18n import _, add_fallback, set_lang
from pylons import tmpl_context as c

import babel
from babel import Locale
import babel.dates


LOCALES = [babel.Locale('de', 'DE')]


def get_default_locale():
    try:
        if c.instance and c.instance.locale:
            return c.instance.locale
        locale = config.get('adhocracy.language', 'en_US')
        return babel.Locale.parse(locale)
    except TypeError:
        return babel.Locale.parse('en_US')


def handle_request():
    """
    Given a request, try to determine the appropriate locale to use for the
    request. When a user is logged in, his or her settings will first be
    queried.
    Otherwise, an appropriate locale will be negotiated between the browser
    accept headers and the available locales.
    """
    from pylons import request, tmpl_context as c
    c.locale = user_language(c.user, request.languages)


def user_language(user, fallbacks=[]):
    # find out the locale
    locale = None
    if user and user.locale:
        locale = user.locale
    else:
        locales = map(str, LOCALES)
        locale = Locale.parse(Locale.negotiate(fallbacks, locales)) \
                 or get_default_locale()

    # determinate from which path we load the translations
    translations_module = config.get('adhocracy.translations', 'adhocracy')
    translations_module_loader = pkgutil.get_loader(translations_module)
    if translations_module_loader is None:
        raise ValueError(('Cannot import the module "%s" configured for '
                          '"adhocracy.translations". Make sure it is an '
                          'importable module (and contains the '
                          'translation files in a subdirectory '
                          '"i18n"') % translations_module)

    translations_root = translations_module_loader.filename
    translations_config = {'pylons.paths': {'root': translations_root},
                           'pylons.package': config.get('pylons.package')}

    # set language and fallback
    set_lang(locale.language, pylons_config=translations_config)
    add_fallback(get_default_locale().language,
                 pylons_config=translations_config)
    formencode.api.set_stdtranslation(domain="FormEncode",
                                      languages=[locale.language])
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
        return babel.dates.format_date(date, 'long', c.locale)


def countdown_time(dt, default):
    # THIS IS A HACK TO GET RID OF BABEL
    if dt is not None:
        delta = dt - datetime.utcnow()
        default = delta.days
    return _("%d days") % default


def format_date(dt):
    from pylons import tmpl_context as c
    ts = babel.dates.format_date(dt, format='long', locale=c.locale or
            babel.Locale('en', 'US'))
    return _("%(ts)s") % {'ts': ts}


def relative_time(dt):
    """ A short statement giving the time distance since ``dt``. """
    fmt = "<time class='ts' datetime='%(iso)sZ'>%(formatted)s</time>"
    return fmt % dict(iso=dt.isoformat(),
                      formatted=format_date(dt))
