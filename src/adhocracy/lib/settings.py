from collections import OrderedDict

from pylons.i18n import lazy_ugettext as L_

from pylons import tmpl_context as c
from adhocracy.lib import helpers as h
from adhocracy import model


INSTANCE_UPDATED_MSG = L_('The changes were saved.')
NO_UPDATE_REQUIRED = L_('No update required.')


def error_formatter(error):
    return '<p class="help-block">%s</p>' % error


def update_attributes(entity, form_result, attributes):
    '''
    Update the given *attributes* on the *entity* object
    with the values in *form_result* and returns if an attribute
    was updated.

    *entity* (:class:`adhocracy.model.Instance`)
       The Instance to update.
    *form_result* (dict)
       A dict, usually the result of a formencode
       validation.
    *attributes* (`list` of `str`)
       The attributes to update.

    Returns: `True` if one of the *attributes* was updated, `False`
    no attribute needed to be updated.

    Raises:

    *AttributeError*
       If the attribute does not exist on the *entity* object.
    *KeyError*
       If the *form_result* dict has no key with the name of the
       attribute.
    '''
    updated = False
    for attribute in attributes:
        new_value = form_result[attribute]
        current_value = getattr(entity, attribute)
        if new_value != current_value:
            setattr(entity, attribute, new_value)
            updated = True
    return updated


class Menu(OrderedDict):
    '''Subclass so we can attach attributes'''

    @classmethod
    def create(cls, entity, current, items):
        menu = cls()
        menu.__setattr__('current', None)

        for k, v in items.iteritems():
            setting = cls._setting(entity, k, *v)
            if setting['allowed']:
                menu[k] = setting
                if k == current:
                    menu.current = setting
                    setting['active'] = True
                    setting['class'] = 'active'
                else:
                    setting['class'] = ''

        if menu.current is None:
            raise ValueError('current ("%s") is no menu item' % current)

        return menu

    @classmethod
    def _setting(cls, entity, name, label, allowed=True, force_url=None):
        return {'name': name,
                'url': cls.settings_url(entity, name, force_url),
                'label': label,
                'allowed': allowed}

    @classmethod
    def settings_url(cls, entity, name, force_url=None):
        full_path = 'settings/%s' % name if force_url is None else force_url
        if isinstance(entity, model.Instance):
            return h.entity_url(entity, member=full_path)
        else:
            return h.entity_url(entity, instance=c.instance, member=full_path)

    def url_for(self, value):
        current = self.get(value)
        if current is None:
            return ValueError('No Menu item named "%s"' % value)
        else:
            return current['url']
