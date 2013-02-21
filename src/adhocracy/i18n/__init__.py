from datetime import datetime, timedelta
import pkgutil

import babel
from babel import Locale
import babel.dates
import formencode
from pylons.i18n import _, add_fallback, set_lang
from pylons import config, tmpl_context as c


LOCALES = [babel.Locale('de', 'DE'),
           babel.Locale('en', 'US'),
           babel.Locale('fr', 'FR'),
           babel.Locale('nl', 'NL'),
           babel.Locale('pl', 'PL'),
           babel.Locale('ro', 'RO'),
           babel.Locale('ru', 'RU')]


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

    try:
        request_languages = request.languages
    except AttributeError:
        # request.languages fails if no accept_language is set
        # becaues of incompatibility between WebOb >= 1.1.1 and Paste-1.7.5.1
        request_languages = []
    c.locale = user_language(c.user, request_languages)


def user_language(user, fallbacks=[]):
    # find out the locale
    locale = None
    if user and user.locale:
        locale = user.locale

    if locale is None:
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
    '''
    Format the date in a local aware format.
    '''
    from pylons import tmpl_context as c
    return babel.dates.format_date(dt, format='long', locale=c.locale or
                                   babel.Locale('en', 'US'))


def format_time(dt):
    '''
    Format the date in a local aware format.
    '''
    from pylons import tmpl_context as c
    return babel.dates.format_time(dt, format='short', locale=c.locale or
                                   babel.Locale('en', 'US'))


def relative_time(dt):
    """ A short statement giving the time distance since ``dt``. """
    fmt = "<time class='ts' datetime='%(iso)sZ'>%(formatted)s</time>"
    dt = dt.replace(microsecond=0)
    formatted = "%s %s" % (format_date(dt), format_time(dt))
    return fmt % dict(iso=dt.isoformat(), formatted=formatted)
