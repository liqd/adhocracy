
import datetime
import re

from adhocracy.lib import votedetail
from adhocracy import config
from adhocracy import model


def _set_optional(o, data, key, export_prefix=''):
    assert o
    external_key = export_prefix + key
    if external_key in data:
        setattr(o, key, data[external_key])


def encode_locale(locale):
    if locale is None:
        return None
    return '_'.join(filter(None, (locale.language, locale.script,
                                  locale.territory, locale.variant)))


def decode_locale(ldata):
    return ldata


def encode_time(dt):
    return dt.isoformat()


def decode_time(s):
    strptime = datetime.datetime.strptime
    try:
        return strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        try:
            return strptime(s, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return strptime(s, '%Y-%m-%dT%H:%M:%S')


class _Transform(object):
    """ Every transform must define:
    * _ID_KEY: The name of the property to be used as key
    * _export(self, obj): A method to export an object to JSON
    * import_all(self, data): The method to import an object from data
    Instead of import_all, the class can also use the default implementation
    and define instead:
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
        if k is None:
            return None
        findm = getattr(self._model_class, 'find_by_' + self._ID_KEY)
        res = findm(k)
        if res is not None:
            key_val = getattr(res, self._ID_KEY)
            assert key_val == k, (
                u'Unexpected value for %s.find_by_%s: expected %r, got %r' %
                (self._model_class.__name__, self._ID_KEY, k, key_val))
        return res

    def _compute_key(self, o):
        return unicode(getattr(o, self._ID_KEY))

    def _compute_key_from_data(self, data):
        return data.get(self._ID_KEY)

    def export_all(self):
        return dict((self._compute_key(o), self._export(o))
                    for o in self._get_all())

    def _get_all(self):
        return self._model_class.all()

    def import_all(self, odict):
        return dict((k, self._import(data)) for k, data in odict.items())

    def _import(self, data):
        obj = self._get_by_key(self._compute_key_from_data(data))
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


class BadgeTransform(_Transform):
    _ID_KEY = 'title'

    def _get_by_key(self, k):
        return self._model_class.find(k)

    def _create(self, data):
        btype = data.get('adhocracy_badge_type', 'user')
        if btype == 'user':
            return model.UserBadge.create(
                title=data['title'],
                color=data.get('color', u''),
                visible=data.get('visible', False),
                description=data.get('description', u''))
        else:
            raise NotImplementedError()

    def _modify(self, obj, data):
        obj.title = data['title']
        _set_optional(obj, data, 'color')
        _set_optional(obj, data, 'visible')
        _set_optional(obj, data, 'description')

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
            if config.get_bool('adhocracy.export_personal_email'):
                self._ID_KEY = 'email'
            else:
                self._ID_KEY = 'user_name'
        else:
            self._ID_KEY = 'id'
            self._get_by_key = self._model_class.find
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
                o.locale = decode_locale(data['locale'])
        if self._opt_password:
            _set_optional(o, data, 'activation_code', 'adhocracy_')
            _set_optional(o, data, 'reset_code', 'adhocracy_')
            _set_optional(o, data, 'password', 'adhocracy_')
            _set_optional(o, data, 'banned', 'adhocracy_')
            _set_optional(o, data, 'welcome_code', 'adhocracy_')
        if self._opt_badges:
            if 'badges' in data:
                old_badges = o.badges
                new_badges = map(self._badge_transform._get_by_key,
                                 data['badges'])
                for b in new_badges:
                    if b not in old_badges:
                        b.assign(o, o)

    def _export(self, o):
        res = {}
        if self._opt_personal:
            res.update({
                'id': o.id,
                'user_name': o.user_name,
                'display_name': o.display_name,
                'bio': o.bio,
                'email': o.email,
                'gender': o.gender,
                'locale': encode_locale(o.locale),
            })
            if config.get('adhocracy.user.optional_attributes'):
                res['optional_attributes'] = o.optional_attributes
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


class InstanceTransform(_Transform):
    _ID_KEY = 'key'

    def __init__(self, options, user_transform, badge_transform):
        super(InstanceTransform, self).__init__(options)
        self._user_transform = user_transform
        self._badge_transform = (
            badge_transform
            if options.get('include_badge', False)
            else None
        )

    def _export(self, obj):
        res = {
            'adhocracy_type': 'instance',
            'key': obj.key,
            'label': obj.label,
            'creator': self._user_transform._compute_key(obj.creator),
            'description': obj.description,
            'adhocracy_required_majority': obj.required_majority,
            'adhocracy_activation_delay': obj.activation_delay,
            'create_time': encode_time(obj.create_time),
            'adhocracy_access_time': encode_time(obj.access_time),
            'adhocracy_delete_time': (encode_time(obj.delete_time)
                                      if obj.delete_time
                                      else None),
            'adhocracy_default_group_id': obj.default_group_id,
            'adhocracy_allow_adopt': obj.allow_adopt,
            'adhocracy_allow_delegate': obj.allow_delegate,
            'adhocracy_allow_propose': obj.allow_propose,
            'adhocracy_allow_index': obj.allow_index,
            'adhocracy_hidden': obj.hidden,
            'locale': encode_locale(obj.locale),
            'adhocracy_css': obj.css,
            'frozen': obj.frozen,
            'adhocracy_milestones': obj.milestones,
            'adhocracy_use_norms': obj.use_norms,
            'adhocracy_require_selection': obj.require_selection,
            'adhocracy_is_authenticated': obj.is_authenticated,
            'adhocracy_hide_global_categories': obj.hide_global_categories,
            'adhocracy_editable_comments_default': (
                obj.editable_comments_default),
            'adhocracy_editable_proposals_default': (
                obj.editable_proposals_default),
            'adhocracy_require_valid_email': obj.require_valid_email,
            'adhocracy_allow_thumbnailbadges': obj.allow_thumbnailbadges,
            'adhocracy_thumbnailbadges_height': obj.thumbnailbadges_height,
            'adhocracy_thumbnailbadges_width': obj.thumbnailbadges_width,
        }
        if self._options.get('include_instance_proposal'):
            ptransform = ProposalTransform(self._options, obj,
                                           self._user_transform)
            res['proposals'] = ptransform.export_all()

        if self._badge_transform and votedetail.is_enabled():
            res['adhocracy_votedetail_userbadges'] = [
                self._badge_transform._compute_key(b)
                for b in obj.votedetail_userbadges
            ]

        return res

    def _create(self, data):
        btype = data.get('adhocracy_type', 'instance')
        if btype == 'instance':
            creator = self._user_transform._get_by_key(data['creator'])
            return model.Instance.create(
                data['key'].lower(),
                data['label'],
                creator)
        else:
            raise NotImplementedError()

    def _modify(self, o, data):
        _set_optional(o, data, 'label')
        if 'creator' in data:
            creator = self._user_transform._get_by_key(data['creator'])
            if creator:
                o.creator = creator
        _set_optional(o, data, 'description')
        _set_optional(o, data, 'required_majority', 'adhocracy_')
        _set_optional(o, data, 'activation_delay', 'adhocracy_')
        if 'create_time' in data:
            o.create_time = decode_time(data['create_time'])
        if 'adhocracy_access_time' in data:
            o.access_time = decode_time(data['adhocracy_access_time'])
        if 'adhocracy_delete_time' in data:
            if data['adhocracy_delete_time'] is None:
                o.delete_time = None
            else:
                o.delete_time = decode_time(data['adhocracy_delete_time'])
        _set_optional(o, data, 'default_group_id', 'adhocracy_')
        _set_optional(o, data, 'allow_adopt', 'adhocracy_')
        _set_optional(o, data, 'allow_delegate', 'adhocracy_')
        _set_optional(o, data, 'allow_propose', 'adhocracy_')
        _set_optional(o, data, 'allow_index', 'adhocracy_')
        _set_optional(o, data, 'hidden', 'adhocracy_')
        if 'locale' in data:
            if data['locale'] is None:
                o.locale = data['locale']
            else:
                o.locale = decode_locale(data['locale'])
        _set_optional(o, data, 'css', 'adhocracy_')
        _set_optional(o, data, 'frozen')
        _set_optional(o, data, 'milestones', 'adhocracy_')
        _set_optional(o, data, 'use_norms', 'adhocracy_')
        _set_optional(o, data, 'require_selection', 'adhocracy_')
        _set_optional(o, data, 'is_authenticated', 'adhocracy_')
        _set_optional(o, data, 'hide_global_categories', 'adhocracy_')
        _set_optional(o, data, 'editable_comments_default', 'adhocracy_')
        _set_optional(o, data, 'editable_proposals_default', 'adhocracy_')
        _set_optional(o, data, 'require_valid_email', 'adhocracy_')
        _set_optional(o, data, 'allow_thumbnailbadges', 'adhocracy_')
        _set_optional(o, data, 'thumbnailbadges_height', 'adhocracy_')
        _set_optional(o, data, 'thumbnailbadges_width', 'adhocracy_')

        if self._options.get('include_instance_proposal'):
            ptransform = ProposalTransform(self._options, o,
                                           self._user_transform)
            ptransform.import_all(data.get('proposals', {}))

        if self._badge_transform and votedetail.is_enabled():
            if 'adhocracy_votedetail_userbadges' in data:
                o.votedetail_userbadges = [
                    self._badge_transform._get_by_key(bid)
                    for bid in data['adhocracy_votedetail_userbadges']
                ]

    def _get_by_key(self, key):
        return self._model_class.find(key)


class ProposalTransform(_Transform):
    _ID_KEY = 'id'

    def __init__(self, options, instance, user_transform):
        super(ProposalTransform, self).__init__(options)
        self._instance = instance
        self._user_transform = user_transform

    def _get_all(self):
        return self._model_class.all_q(self._instance)

    def _create(self, data):
        btype = data.get('adhocracy_type', 'proposal')
        if btype == 'proposal':
            creator = self._user_transform._get_by_key(data['creator'])
            assert creator
            label = data['title']
            desc = data['description']
            o = self._model_class.create(self._instance, label, creator)
            description = model.Page.create(
                self._instance,
                label,
                desc,
                creator,
                function=model.Page.DESCRIPTION,
                formatting=True)
            description.parents = [o]
            o.description = description
            return o
        else:
            raise NotImplementedError()

    def _modify(self, o, data):
        pass

    def _export(self, obj):
        res = {
            'id': obj.id,
            'title': obj.title,
            'create_time': encode_time(obj.create_time),
            'description': (None if obj.description is None
                            else obj.description.head.text),
            'creator': self._user_transform._compute_key(obj.creator),
            'adhocracy_type': 'proposal',
            'category': obj.category.title if obj.category else None,
            'tags': [o.name for o, _ in obj.tags],
            'badges': [o.badge.title for o in obj.delegateablebadges
                       if o.badge.polymorphic_identity != 'category'],
        }
        if self._options.get('include_proposal_creator_badges', False):
            res['creator_badges'] = [o.badge.title
                                     for o in obj.creator.userbadges],
        if self._options.get('include_ratings', False):
            res.update({
                'rate_pro': obj.rate_poll.tally.num_for,
                'rate_contra': obj.rate_poll.tally.num_against,
                'rate_neutral': obj.rate_poll.tally.num_abstain,
            })
            if votedetail.is_enabled():
                vd = votedetail.calc_votedetail_dict(
                    obj.instance, obj.rate_poll, badge_title_only=True)
                if vd:
                    res['votedetail_rate_poll'] = vd

        if self._options.get('include_instance_proposal_comment', False):
            ctransform = CommentTransform(self._options,
                                          obj.description.comments,
                                          None,
                                          self._user_transform)
            res['comments'] = ctransform.export_all()
        return res


class CommentTransform(_Transform):
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
            'create_time': encode_time(obj.create_time),
            'text': obj.latest.text,
            'sentiment': obj.latest.sentiment,
            'creator': self._user_transform._compute_key(obj.creator),
            'adhocracy_type': 'comment',
        }
        if self._options.get('include_ratings', False):
            res.update({
                'rate_pro': obj.poll.tally.num_for,
                'rate_contra': obj.poll.tally.num_against,
                'rate_neutral': obj.poll.tally.num_abstain,
            })
        ct = CommentTransform(self._options, self._all_comments, obj,
                              self._user_transform)
        res['comments'] = ct.export_all()
        return res


class RequestLogTransform(_Transform):
    _ID_KEY = 'id'

    def __init__(self, options):
        super(RequestLogTransform, self).__init__(options)

    def _export(self, obj):
        res = obj.to_dict()
        res['access_time'] = encode_time(res['access_time'])
        return res


class StaticPageTransform(_Transform):
    def __init__(self, options, backend=None):
        super(StaticPageTransform, self).__init__(options)
        if backend is None:
            from adhocracy.lib.staticpage import get_backend
            backend = get_backend()
        self._backend = backend

    def _export(self, obj):
        return {
            'key': obj.key,
            'lang': obj.lang,
            'title': obj.title,
            'body': obj.body
        }

    def _create(self, data):
        return self._backend.create(
            data['key'],
            data['lang'],
            data.get('title', u''),
            data.get('body', u''))

    def _modify(self, o, data):
        _set_optional(o, data, 'key')
        _set_optional(o, data, 'lang')
        _set_optional(o, data, 'title')
        _set_optional(o, data, 'body')

    def _get_by_key(self, k):
        key, _, lang = k.partition(u'_')
        return self._backend.get(key, [lang])

    def _get_all(self):
        return self._backend.all()

    def _compute_key(self, obj):
        return obj.key + u'_' + obj.lang

    def _compute_key_from_data(self, data):
        return data['key'] + u'_' + data['lang']


def gen_all(options):
    badge_transform = BadgeTransform(options)
    user_transform = UserTransform(options, badge_transform)
    instance_transform = InstanceTransform(
        options, user_transform, badge_transform)
    requestlog_transform = RequestLogTransform(options)
    staticpage_transform = StaticPageTransform(options)
    return [badge_transform, user_transform, instance_transform,
            requestlog_transform, staticpage_transform]


def gen_active(options):
    return [tf for tf in gen_all(options)
            if options.get('include_' + tf.name.lower(), False)]
