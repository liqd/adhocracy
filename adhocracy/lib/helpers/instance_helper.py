import url as _url


def url(instance, member=None, format=None, **kwargs):
    return _url.build(instance, 'instance', instance.key,
                      member=member, format=format, **kwargs)


def breadcrumbs(instance):
    bc = _url.root()
    return bc
