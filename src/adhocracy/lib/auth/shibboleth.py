from pylons import config


def get_userbadge_mapping(config=config):
    mapping = config.get('adhocracy.shibboleth.userbadge_mapping', u'')
    return (line.strip().split(u' ')
            for line in mapping.strip().split(u'\n')
            if line is not u'')


def _attribute_equals(request, key, value):
    """
    exact match
    """
    return request.headers.get(key) == value


def _attribute_contains(request, key, value):
    """
    contains element
    """
    elements = (e.strip() for e in request.headers.get(key).split(','))
    return value in elements


def _attribute_contains_substring(request, key, value):
    """
    contains substring
    """
    return value in request.headers.get(key)


USERBADGE_MAPPERS = {
    'attribute_equals': _attribute_equals,
    'attribute_contains': _attribute_contains,
    'attribute_contains_substring': _attribute_contains_substring,
}
