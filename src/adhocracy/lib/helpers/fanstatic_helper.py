'''
helper functions to work with fanstatic
'''

from js.socialshareprivacy import library
import fanstatic


def get_socialshareprivacy_url():
    '''
    call this after you need()ed socialshareprivacy!
    Returns the url from which socialshareprivacy will be shipped.
    '''
    return fanstatic.get_needed().library_url(library)


def _get_resource(module, name):
    resource = getattr(module, name, None)
    if resource is None:
        raise AttributeError('"%s" does not exist' % name)
    if not isinstance(resource, (fanstatic.Resource, fanstatic.Group)):
        raise ValueError('"%s" is not a valid Resource' % name)
    return resource


class FanstaticNeedHelper(object):
    '''
    A helper class to access fanstatic resources
    defined in :module:`adhocracy.static`

    Use it this way::

        from adhocracy import static
        need = FanstaticNeedHelper(static)
        need.stylesheets

    where "stylesheets" is a fanstatic Resource or Group defined
    in adhocracy.static.
    '''

    def __init__(self, module):
        self.module = module

    def __getattr__(self, name):
        return _get_resource(self.module, name).need()
