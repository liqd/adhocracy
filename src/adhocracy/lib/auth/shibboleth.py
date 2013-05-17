from pylons import config


def get_userbadge_mapping(config=config):
    mapping = config.get('adhocracy.shibboleth.userbadge_mapping', u'')
    return (line.strip().split(u' ')
            for line in mapping.strip().split(u'\n')
            if line is not u'')


def _attribute_equals(request, key, value):
    return request.headers.get(key) == value


USERBADGE_MAPPERS = {
    'attribute_equals': _attribute_equals,
}
