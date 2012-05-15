'''
helper functions to work with fanstatic
'''

import fanstatic


class FanstaticNeedHelper(object):
    '''
    A helper class to access fanstatic resources
    defined in :module:`adhocracy.static`

    Use it this way::

        from adhocracy import static
        need = Need(static)
        need.stylesheets

    where "stylesheets" is a fanstatic Resource or Group defined
    in adhocracy.static.
    '''

    def __init__(self, module):
        self.module = module

    def __getattr__(self, name):
        resource = getattr(self.module, name, None)
        if resource is None:
            raise AttributeError('"%s" does not exist' % name)
        if not isinstance(resource, (fanstatic.Resource, fanstatic.Group)):
            raise ValueError('"%s" is not a valid Resource' % name)
        return resource.need()
