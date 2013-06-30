from paste.deploy.converters import asbool
from paste.deploy.converters import asint
from paste.deploy.converters import aslist
from pylons import config


DEFAULTS = {
    'adhocracy.enable_gender': False,
    'adhocracy.feedback_check_instance': True,
    'adhocracy.force_randomized_user_names': False,
    'adhocracy.hide_locallogin': False,
    'adhocracy.require_email': True,
    'adhocracy.set_display_name_on_register': False,
    'adhocracy.use_feedback_instance': False,
    'adhocracy.feedback_use_categories': True,
}


def get_value(key, converter, default=None, config=config):

    value = config.get(key)

    if value is None:
        if default is not None:
            return default
        else:
            return DEFAULTS.get(key)

    if converter is None:
        return value
    else:
        return converter(value)


def get_bool(key, default=None, config=config):
    return get_value(key, asbool, default)


def get_int(key, default=None, config=config):
    return get_value(key, asint, default)


def get_list(key, default=None, config=config):
    return get_value(key, aslist, default)


def get(key, default=None, config=config):
    return get_value(key, None, default)
