
import babel.core
import hashlib
import os
import re
import time

from adhocracy import model


def _set_optional(o, data, key, export_prefix=''):
    assert o
    external_key = export_prefix + key
    if external_key in data:
        setattr(o, key, data[external_key])


def _encode_locale(locale):
    return '_'.join(filter(None, (locale.language, locale.script,
                                  locale.territory, locale.variant)))


def _decode_locale(ldata):
    return ldata


class _Transform(object):
    """ Every transform must define:
    * _ID_KEY: The name of the property to be used as key
    * _export(self, obj): A method to export an object to JSON
    * import_all(self, data): The method to import an object from data
    Instead of import_all, the class can also use the default implementation and define instead:
    * _create(data) - Create a new object with the minimum set of properties
    * _modify(obj, data) - Modify an object to have the specified properties
    """

    def __init__(self, options):
        self._options = options
        self.name = re.match(r'^(.*)Transform$', type(self).__name__).group(1)
        self.public_name = self.name.lower()
        self._model_class = getattr(model, self.name)

    def _get_by_key(self, k):
        """ Returns None if the object cannot be found,
        and the local object in database otherwise. """
        findm = getattr(self._model_class, 'find_by_' + self._ID_KEY)
        res = findm(k)
        if res is not None:
            assert getattr(res, self._ID_KEY) == k
        return res

    def _compute_key(self, o):
        return str(getattr(o, self._ID_KEY))

    def export_all(self):
        return dict((self._compute_key(o), self._export(o))
                    for o in self._get_all())

    def _get_all(self):
        return self._model_class.all()

    def import_all(self, odict):
        return dict((k, self._import(data)) for k, data in odict.items())

    def _import(self, data):
        obj = self._get_by_key(data[self._ID_KEY])
        if obj:
            doUpdate = self._replacement_strategy == 'update'
        else:
            obj = self._create(data)
            doUpdate = True

        if doUpdate:
            self._modify(obj, data)
        model.meta.Session.add(obj)
        return obj

    @property
    def _replacement_strategy(self):
        return self._options.get('replacement_strategy', 'update')


class _ExportOnlyTransform(_Transform):
    def import_(self, odict, replacement_strategy):
        raise NotImplementedError()


class BadgeTransform(_Transform):
    _ID_KEY = 'title'

    def _get_by_key(self, k):
        return self._model_class.find(k)

    def _create(self, data):
        btype = data.get('adhocracy_badge_type', 'user')
        if btype == 'user':
            return model.UserBadge.create(
                title=data['title'],
                color=data['color'],
                visible=data['visible'],
                description=data['description'])
        else:
            raise NotImplementedError()

    def _modify(self, obj, data):
        obj.title = data['title']
        obj.color = data['color']
        obj.visible = data['visible']
        obj.description = data['description']

    def _export(self, obj):
        return {
            'title': obj.title,
            'color': obj.color,
            'visible': obj.visible,
            'description': obj.description,
            'adhocracy_badge_type': obj.polymorphic_identity,
        }


class UserTransform(_Transform):
    """
    Option keys:
    - user_personal - Include identifying information
    - user_password - Include authentication information
    - include_badges - Include a list of badges that the user has
    """
    def __init__(self, options, badge_transform):
        super(UserTransform, self).__init__(options)
        self._badge_transform = badge_transform
        self._opt_personal = self._options.get('user_personal', False)
        if self._opt_personal:
            self._ID_KEY = 'email'
        else:
            self._ID_KEY = 'id'
        self._opt_password = self._options.get('user_password', False)
        self._opt_badges = self._options.get('include_badge', False)
        self._opt_welcome = self._options.get('welcome', False)

    def _create(self, data):
        assert self._opt_personal
        res = self._model_class.create(data['user_name'], data['email'])
        res.activation_code = None
        if self._opt_welcome:
            res.initialize_welcome()
        return res

    def _modify(self, o, data):
        assert self._opt_personal
        if self._opt_personal:
            _set_optional(o, data, 'user_name')
            _set_optional(o, data, 'display_name')
            _set_optional(o, data, 'bio')
            _set_optional(o, data, 'email')
            _set_optional(o, data, 'gender')
            if 'locale' in data:
                o.locale = _decode_locale(data['locale'])
        if self._opt_password:
            _set_optional(o, data, 'activation_code', 'adhocracy_')
            _set_optional(o, data, 'reset_code', 'adhocracy_')
            _set_optional(o, data, 'password', 'adhocracy_')
            _set_optional(o, data, 'banned', 'adhocracy_')
            _set_optional(o, data, 'welcome_code', 'adhocracy_')
        if self._opt_badges:
            o.badges = list(map(self._badge_transform._get_by_key,
                                data['badges']))

    def _export(self, o):
        res = {}
        if self._opt_personal:
            res.update({
                'user_name': o.user_name,
                'display_name': o.display_name,
                'bio': o.bio,
                'email': o.email,
                'gender': o.gender,
                'locale': _encode_locale(o.locale),
            })
        if self._opt_password:
            res.update({
                'adhocracy_activation_code': o.activation_code,
                'adhocracy_reset_code': o.reset_code,
                'adhocracy_password': o.password,
                'adhocracy_banned': o.banned,
                'adhocracy_welcome_code': o.welcome_code,
            })
        if self._opt_badges:
            res['badges'] = [getattr(b, BadgeTransform._ID_KEY)
                             for b in o.badges]
        return res


class InstanceTransform(_ExportOnlyTransform):
    _ID_KEY = 'key'

    def __init__(self, options, user_transform):
        super(InstanceTransform, self).__init__(options)
        self._user_transform = user_transform

    def _export(self, obj):
        res = {
            'adhocracy_type': 'instance',
            'key': obj.key,
            'label': obj.label,
            'creator': self._user_transform._compute_key(obj.creator)
        }
        if self._options.get('include_instance_proposals'):
            ptransform = ProposalTransform(self._options, obj,
                                           self._user_transform)
            res['proposals'] = ptransform.export_all()

        return res


class ProposalTransform(_ExportOnlyTransform):
    _ID_KEY = 'id'

    def __init__(self, options, instance, user_transform):
        super(ProposalTransform, self).__init__(options)
        self._instance = instance
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
            ctransform = CommentTransform(self._options,
                                          obj.description.comments,
                                          None,
                                          self._user_transform)
            res['comments'] = ctransform.export_all()
        return res


class CommentTransform(_ExportOnlyTransform):
    _ID_KEY = 'id'

    def __init__(self, options, all_comments, parent_comment, user_transform):
        super(CommentTransform, self).__init__(options)
        self._all_comments = all_comments
        self._parent_comment = parent_comment
        self._user_transform = user_transform

    def _get_all(self):
        return [c for c in self._all_comments
                if c.reply == self._parent_comment]

    def _export(self, obj):
        res = {
            'text': obj.latest.text,
            'sentiment': obj.latest.sentiment,
            'creator': self._user_transform._compute_key(obj.creator),
            'adhocracy_type': 'comment',
        }
        ct = CommentTransform(self._options, self._all_comments, obj,
                              self._user_transform)
        res['comments'] = ct.export_all()
        return res


def gen_all(options):
    badge_transform = BadgeTransform(options)
    user_transform = UserTransform(options, badge_transform)
    instance_transform = InstanceTransform(options, user_transform)
    return [badge_transform, user_transform, instance_transform]


def gen_active(options):
    return [tf for tf in gen_all(options)
            if options.get('include_' + tf.name.lower(), False)]
