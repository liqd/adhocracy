
import hashlib
import os
import re
import time

from adhocracy import model

class _Transform(object):
    def __init__(self, options):
        pass

    @property
    def name(self):
        m = re.match(r'^(.*)Transform$', type(self).__name__)
        assert m
        return m.group(1)

    @property
    def public_name(self):
        return self.name.lower() 

    @property
    def _model_class(self):
        return getattr(model, self.name)

    def _gen_prop_names(self):
        self._prop_names_stored = dict(
            (p, p[len('adhocracy_'):] if p.startswith('adhocracy_') else p)
            for p in self._PROPS
        )

    @property
    def _prop_names(self):
        if not hasattr('self', '_prop_names_stored'):
            self._gen_prop_names()
        return self._prop_names_stored

    def _get_by_key(self, k):
        findm = getattr(self.model, 'find_by_' + self._ID_KEY)
        res = findm(k)
        assert getattr(res, self._ID_KEY)
        return res

    def _compute_key(self, o):
        return getattr(o, self._ID_KEY)

    def export_all(self):
        return dict((self._compute_key(o), self._export_object(o))
                    for o in self._model_class.all())

    def _extract_prop(self, obj, native_name):
        return getattr(obj, native_name)

    def _export_object(self, obj):
        data = dict((public_name, self._extract_prop(obj, native_name))
            for public_name,native_name in self._prop_names.items())
        for p,val in getattr(self, '_ENFORCED_PROPS', {}):
            data[p] = val
        return data

    def _init_object(self, obj, data):
        for r in self._REQUIRED:
            setattr(obj, self._prop_names[r], data[r])
        for public_name,native_name in self._prop_names.items():
            if native_name in data:
                setattr(obj, public_name, data[native_name])

    def import_objects(self, odict, replacement_strategy):
        return dict((k, self._import_object(data, replacement_strategy)) for k,data in odict.items())

    def _import_object(self, data, replacement_strategy):
        for p,val in getattr(self, '_ENFORCED_PROPS', {}):
            assert data[p] == val
        current = self._get_by_key(data[self._ID_KEY])
        if current:
            doUpdate = replacement_strategy == 'update'
        else:
            start_props = dict((data[self._prop_names[r]]) for r in self._REQUIRED)
            res = self._model_class.create(**start_props)
            doUpdate = True

        if doUpdate:
            self._init_object(res, data)
        model.meta.session.add(res)
        return res


class BadgeTransform(_Transform):
    _PROPS = ['title', 'color', 'description']
    _REQUIRED = _PROPS
    _ID_KEY = 'title'


class UserTransform(_Transform):
    """
    Option keys:
    - user_personal - Include identifying information
    - user_password - Include authentication information
    - include_badges - Include a list of badges that the user has
    """
    def __init__(self, options, badge_transform):
        self._PROPS = []
        if options.get('user_personal', False):
            self._PROPS.extend(['user_name', 'display_name', 'bio',
                                'email', 'locale'])
            self._ID_KEY = 'user_name'
        else:
            self._ID_KEY = 'id'
            self._compute_key = lambda o: str(getattr(o, self._ID_KEY))
        if options.get('user_password', False):
            self._PROPS.extend(['adhocracy_activation_code',
              'adhocracy_reset_code', 'adhocracy_password', 'adhocracy_banned'])
        if options.get('include_badges', False):
            self._badge_transform = badge_transform

    def _export_object(self, o):
        data = super(UserTransform, self)._export_object(o)
        if hasattr(self, '_badge_transform'):
            data['badges'] = list(map(self._badge_transform._compute_key, o.badges))
        return data

    def _init_object(self, obj, data):
        super(UserTransform, self)._init_object(obj, data)
        if hasattr(self, '_badge_transform'):
            obj.badges = list(map(self._badge_transform._get_by_key, data['badges']))
        return res

    def _extract_prop(self, obj, name):
        if name == 'locale':
            return str(obj.locale)
        return super(UserTransform, self)._extract_prop(obj, name)



class InstanceTransform(_Transform):
    _ID_KEY = 'key'
    _REQUIRED = ['key', 'label', 'creator']
    _PROPS = ['key', 'label', 'description']
    _ENFORCED_PROPS = {'adhocracy_type': 'instance'}

    def __init__(self, options, user_transform):
        if options.get('include_user', False):
            pass


    # TODO special creator
    # TODO proposals

    def _export_object(self, obj):
        data = super(InstanceTransform, self)._export_object(obj)
        
        return data

    def _import_object(self, data, replacement_strategy):        
        return super(InstanceTransform, self)._import_object(data, replacement_strategy)


def gen_all(options):
    badge_transform = BadgeTransform(options)
    user_transform = UserTransform(options, badge_transform)
    return [badge_transform, user_transform]

def gen_active(options):
    return [tf for tf in gen_all(options) if options.get('include_' + tf.name.lower(), False)]

