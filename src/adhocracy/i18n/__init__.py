from datetime import datetime, timedelta
import logging
import pkgutil

import pytz
import babel
from babel import Locale
import babel.dates
import formencode
from pylons.i18n import _, add_fallback, set_lang
from pylons import config, tmpl_context as c


log = logging.getLogger(__name__)


LOCALES = [babel.Locale('de', 'DE'),
           babel.Locale('en', 'US'),
           babel.Locale('fr', 'FR'),
           babel.Locale('nl', 'NL'),
           babel.Locale('pl', 'PL'),
           babel.Locale('ro', 'RO'),
           babel.Locale('ru', 'RU')]
FALLBACK_TZ = 'Europe/Berlin'


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


def countdown_time(dt, default):
    # THIS IS A HACK TO GET RID OF BABEL
    if dt is not None:
        delta = dt - datetime.utcnow()
        default = delta.days
    return _("%d days") % default


def local_datetime(dt):
    """
    Calculates a datetime object with the configured timezone information set
    from a given datetime ``dt``.
    """
    tz_setting = config.get('adhocracy.timezone', FALLBACK_TZ)
    try:
        tz = pytz.timezone(tz_setting)
    except pytz.UnknownTimeZoneError:
        log.warn('Invalid time zone setting: %s' % tz_setting)
        tz = pytz.timezone(FALLBACK_TZ)

    if dt.tzinfo is None:
        return tz.fromutc(dt)
    else:
        return dt.astimezone(tz)


def format_date(dt, set_timezone=True):
    '''
    Format the date in a local aware format.
    '''
    from pylons import tmpl_context as c
    if set_timezone:
        dt = local_datetime(dt)
    return babel.dates.format_date(dt, format='long', locale=c.locale or
                                   babel.Locale('en', 'US'))


def format_time(dt, set_timezone=True):
    '''
    Format the date in a local aware format.
    '''
    from pylons import tmpl_context as c
    if set_timezone:
        dt = local_datetime(dt)
    return babel.dates.format_time(dt, format='short', locale=c.locale or
                                   babel.Locale('en', 'US'))


def date_tag(dt):
    """ Display a <time> html tag for the given datetime ``dt``. """
    fmt = "<time datetime='%(iso)s'>%(formatted)s</time>"
    dt = dt.replace(microsecond=0)
    dt = local_datetime(dt)

    formatted = format_date(dt, False)
    return fmt % dict(iso=dt.isoformat(), formatted=formatted)


def datetime_tag(dt):
    """
    Display a <time> html tag for the given datetime ``dt``.
    """
    fmt = "<time class='ts' datetime='%(iso)s'>%(formatted)s</time>"
    dt = dt.replace(microsecond=0)
    tz_dt = local_datetime(dt)

    formatted = "%s %s" % (format_date(dt), format_time(dt))
    return fmt % dict(iso=tz_dt.isoformat(), formatted=formatted)
