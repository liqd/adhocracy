
import babel.core
import hashlib
import os
import re
import time

from adhocracy import model

def _set_optional(o, data, key, export_prefix=''):
    external_key = export_prefix + key
    if external_key in data:
        setattr(o, key, data[external_key])

def _encode_locale(locale):
    return '_'.join(filter(None, (locale.language, locale.script, locale.territory, locale.variant)))

def _decode_locale(ldata):
    return babel.core.parse_locale(ldata)

class _Transform(object):
    """ Every transform must define:
    * _ID_KEY: The name of the property to be used as key
    * _export(self, obj): A method to export an object to JSON
    * _import(self, data, replacement_strategy): The method to import an object from data
    Instead of _import, the class can also use the default implementation and define instead:
    * _create(data) - Create a new object with the minimum set of properties
    * _modify(obj, data) - Modify an object to have the specified properties
    """

    def __init__(self):
        self.name = re.match(r'^(.*)Transform$', type(self).__name__).group(1)
        self.public_name = self.name.lower()
        self._model_class = getattr(model, self.name)

    def _get_by_key(self, k):
        findm = getattr(self._model_class, 'find_by_' + self._ID_KEY)
        res = findm(k)
        assert getattr(res, self._ID_KEY) == k
        return res

    def _compute_key(self, o):
        return str(getattr(o, self._ID_KEY))

    def export_all(self):
        return dict((self._compute_key(o), self._export(o))
                    for o in self._get_all())

    def _get_all(self):
        return self._model_class.all()

    def import_objects(self, odict, replacement_strategy):
        return dict((k, self._import_object(data, replacement_strategy)) for k,data in odict.items())

    def _import(self, data, replacement_strategy):
        current = self._get_by_key(data[self._ID_KEY])
        if current:
            doUpdate = replacement_strategy == 'update'
        else:
            self._create(data)
            doUpdate = True

        if doUpdate:
            self._modify(res, data)
        model.meta.session.add(res)
        return res


class BadgeTransform(_Transform):
    _ID_KEY = 'title'

    def _create(self, data):
        self._model_class.create(data['title'], data['color'], data['description'])

    def _modify(self, obj, data):
        obj.title = data['title']
        obj.color = data['color']
        obj.description = data['description']

    def _export(self, obj):
        return {
            'title': obj.title,
            'color': obj.color,
            'description': obj.description
        }


class UserTransform(_Transform):
    """
    Option keys:
    - user_personal - Include identifying information
    - user_password - Include authentication information
    - include_badges - Include a list of badges that the user has
    """
    def __init__(self, options):
        super(UserTransform, self).__init__()
        self._opt_personal = options.get('user_personal', False)
        if self._opt_personal:
            self._ID_KEY = 'user_name'
        else:
            self._ID_KEY = 'id'
        self._opt_password = options.get('user_password', False)
        self._opt_badges = options.get('include_badges', False)

    def _create(self, data):
        assert self._opt_personal
        return self._model_class.create(data['user_name'], data['email'])

    def _modify(self, o, data):
        assert self._opt_personal
        if self._opt_personal:
            _set_optional(o, data, 'user_name')
            _set_optional(o, data, 'display_name')
            _set_optional(o, data, 'bio')
            _set_optional(o, data, 'email')
            if 'locale' in data:
                o.locale = _decode_locale(data['locale'])
        if self._opt_password:
            _set_optional(o, data, 'activation_code', 'adhocracy_')
            _set_optional(o, data, 'reset_code', 'adhocracy_')
            _set_optional(o, data, 'password', 'adhocracy_')
            _set_optional(o, data, 'banned', 'adhocracy_')
        if self._opt_badges:
            o.badges = list(map(self._badge_transform._get_by_key, data['badges']))

    def _export(self, o):
        res = {}
        if self._opt_personal:
            res.update({
                'user_name': o.user_name,
                'display_name': o.display_name,
                'bio': o.bio,
                'email': o.email,
                'locale': _encode_locale(o.locale),
            })
        if self._opt_password:
            res.update({
                'adhocracy_activation_code': o.activation_code,
                'adhocracy_reset_code': o.reset_code,
                'adhocracy_password': o.password,
                'adhocracy_banned': o.banned,
            })
        if self._opt_badges:
            res['badges'] = [getattr(b, BadgeTransform._ID_KEY) for b in o.badges]
        return res

class InstanceTransform(_Transform):
    _ID_KEY = 'key'

    def __init__(self, options, user_transform):
        super(InstanceTransform, self).__init__()
        self._options = options
        self._user_transform = user_transform

    def _create(self, data):
        creator = model.user.find_by_id('admin')
        return self._model_class.create(data['key'], data['label'], creator)

    def _export(self, obj):
        res = {
            'adhocracy_type': 'instance',
            'key': obj.key,
            'label': obj.label,
            'creator': self._user_transform._compute_key(obj.creator)
        }
        if self._options.get('include_instance_proposals'):
            ptransform = ProposalTransform(obj, self._options, self._user_transform)
            res['proposals'] = ptransform.export_all()

        return res

    def _import_object(self, data, replacement_strategy):
        return super(InstanceTransform, self)._import_object(data, replacement_strategy)


class ProposalTransform(_Transform):
    _ID_KEY = 'id'

    def __init__(self, instance, options, user_transform):
        super(ProposalTransform, self).__init__()
        self._instance = instance
        self._options = options
        self._user_transform = user_transform

    def _get_all(self):
        return self._model_class.all_q(self._instance)

    def _export(self, obj):
        res = {
            'id': obj.id,
            'title': obj.title,
            'description': obj.description,
            'creator': self._user_transform._compute_key(obj.creator),
            'adhocracy_type': 'proposal',
        }
        if self._options.get('include_instance_proposal_comments', False):
            if obj.description:
                ctransform = CommentTransform(obj.description.comments, None, self._user_transform)
                res['comments'] = ctransform.export_all()
            else:
                res['comments'] = {}
        return res

class CommentTransform(_Transform):
    _ID_KEY = 'id'

    def __init__(self, all_comments, parent_comment, user_transform):
        self._all_comments = all_comments
        self._parent_comment = parent_comment
        self._user_transform = user_transform

    def _get_all(self):
        return [c for c in self._all_comments if c.reply == self._parent_comment]

    def _export(self, obj):
        res = {
            'text': obj.latest.text,
            'sentiment': obj.latest.sentiment,
            'creator': self._user_transform._compute_key(obj.creator),
            'adhocracy_type': 'comment',
        }
        ct = CommentTransform(self._all_comments, obj, self._user_transform)
        res['comments'] = ct.export_all()
        return res


def gen_all(options):
    badge_transform = BadgeTransform()
    user_transform = UserTransform(options)
    instance_transform = InstanceTransform(options, user_transform)
    return [badge_transform, user_transform, instance_transform]

def gen_active(options):
    return [tf for tf in gen_all(options) if options.get('include_' + tf.name.lower(), False)]

