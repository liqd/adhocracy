from pylons import config


def get_userbadge_mapping():
    mapping = config.get('adhocracy.shibboleth.userbadge_mapping', '')
    return (line.strip().split(' ') for line in mapping.strip().split('\n'))


def _attribute_equals(request, key, value):
    return request.headers.get(key) == value


USERBADGE_MAPPERS = {
    'attribute_equals': _attribute_equals,
}
