from paste.deploy.converters import asbool
from paste.deploy.converters import asint
from paste.deploy.converters import aslist
from pylons import config


DEFAULTS = {
}


def get_value(key, converter, default=None):

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


def get_bool(key, default=None):
    return get_value(key, asbool, default)


def get_int(key, default=None):
    return get_value(key, asint, default)


def get_list(key, default=None):
    return get_value(key, aslist, default)


def get(key, default=None):
    return get_value(key, None, default)
