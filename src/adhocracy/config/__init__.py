from paste.deploy.converters import asbool
from paste.deploy.converters import asint
from paste.deploy.converters import aslist
from pylons import config
from pylons.i18n import _


DEFAULTS = {
    'adhocracy.delay_update_queue_seconds': 1,
    'adhocracy.enable_gender': False,
    'adhocracy.feedback_check_instance': True,
    'adhocracy.feedback_instance_key': u'feedback',
    'adhocracy.feedback_use_categories': True,
    'adhocracy.force_randomized_user_names': False,
    'adhocracy.hide_locallogin': False,
    'adhocracy.instance_key_length_max': 20,
    'adhocracy.instance_key_length_min': 4,
    'adhocracy.instance_stylesheets': [],
    'adhocracy.number_instance_overview_milestones': 3,
    'adhocracy.protocol': u'http',
    'adhocracy.relative_urls': False,
    'adhocracy.require_email': True,
    'adhocracy.set_display_name_on_register': False,
    'adhocracy.show_instance_overview_events': True,
    'adhocracy.show_instance_overview_milestones': True,
    'adhocracy.show_instance_overview_proposals_new': True,
    'adhocracy.show_instance_overview_proposals_all': False,
    'adhocracy.show_instance_overview_stats': True,
    'adhocracy.use_feedback_instance': False,
    'adhocracy.user.optional_attributes': [],
}


def get_value(key, converter, default=None, config=config,
              converter_kwargs={}):

    value = config.get(key)

    if value is None:
        if default is not None:
            return default
        else:
            return DEFAULTS.get(key)

    if converter is None:
        return value
    else:
        return converter(value, **converter_kwargs)


def get_bool(key, default=None, config=config):
    return get_value(key, asbool, default, config)


def get_int(key, default=None, config=config):
    return get_value(key, asint, default, config)


def get_list(key, default=None, config=config, sep=','):
    return get_value(key, aslist, default, config, {'sep': sep})


def get(key, default=None, config=config):
    return get_value(key, lambda x: x.decode('utf-8'), default, config)


def get_tuples(key, default=[], sep=u' '):
    mapping = get(key, None)
    if mapping is None:
        return default
    return ((v.strip() for v in line.split(sep))
            for line in mapping.strip().split(u'\n')
            if line is not u'')


def get_optional_user_attributes():

    TYPES = {
        'unicode': (unicode, lambda v: v.decode('utf-8')),
        'int': (int, int),
        'bool': (bool, asbool),
    }

    def transform(key, type_string, label):
        allowed = get_list('adhocracy.user.optional_attributes.%s' % key, None,
                           sep=';')
        type_, converter = TYPES[type_string]
        if allowed is not None:
            allowed = [{
                'value': converter(v),
                'selected': False,
                'label': converter(v),
            } for v in allowed]

            allowed.insert(0, {
                'value': '',
                'selected': True,
                'label': _(u'Keine Angabe')
            })
        return (key, type_, converter, label, allowed)

    return map(lambda t: transform(*t),
               get_tuples('adhocracy.user.optional_attributes', sep=u','))
