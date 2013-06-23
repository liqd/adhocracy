import logging

import adhocracy.model as model
from adhocracy.config import get_bool as config_get_bool
from adhocracy.lib.auth.authentication import allowed_login_types
from adhocracy.lib.helpers.site_helper import get_domain_part

from paste.deploy.converters import asbool

log = logging.getLogger(__name__)

ADMIN = u'admin'
ADMIN_PASSWORD = u'password'


def mk_group(name, code):
    group = model.Group.by_code(unicode(code))
    if not group:
        log.debug("Creating group: %s" % name)
        group = model.Group(unicode(name), unicode(code))
        model.meta.Session.add(group)
    else:
        group.group_name = unicode(name)
    return group


def mk_perm(name):
    perm = model.Permission.find(name)
    if perm is None:
        log.debug("Creating permission: %s" % name)
        perm = model.Permission(name)
        model.meta.Session.add(perm)
        return perm
    return None


def setup_entities(config, initial_setup):
    #model.meta.Session.begin()
    model.meta.Session.commit()

    # administrate installation wide
    admins = mk_group("Administrator", model.Group.CODE_ADMIN)
    organization = mk_group("Organization", model.Group.CODE_ORGANIZATION)
    # administrate instance
    supervisor = mk_group("Supervisor", model.Group.CODE_SUPERVISOR)
    moderator = mk_group("Moderator", model.Group.CODE_MODERATOR)
    voter = mk_group("Voter", model.Group.CODE_VOTER)
    observer = mk_group("Observer", model.Group.CODE_OBSERVER)
    advisor = mk_group("Advisor", model.Group.CODE_ADVISOR)
    default = mk_group("Default", model.Group.CODE_DEFAULT)
    anonymous = mk_group("Anonymous", model.Group.CODE_ANONYMOUS)
    addressee = mk_group("Addressee", model.Group.CODE_ADDRESSEE)

    model.meta.Session.commit()

    # To simplify initial configuration, we allow to define permission
    # includes, e.g. permissions granted to observers are automatically granted
    # to advisors and organizations as well. This is resolved recursively.
    # Note that this applies only to the initial setup.

    def included_groups(groups):
        all_groups = set(groups)
        includes = set()
        for group in groups:
            includes = includes.union(perm_includes.get(group, []))
        for include in includes:
            all_groups = all_groups.union(included_groups(includes))
        return list(all_groups)

    perm_includes = {
        anonymous: [observer],
        observer: [advisor, organization],
        advisor: [voter],
        voter: [moderator, addressee],
        moderator: [supervisor],
        supervisor: [admins],
    }

    default_permission_groups = {
        u'abuse.report': [anonymous],
        u'badge.index': [anonymous],
        u'comment.create': [advisor],
        u'comment.delete': [moderator],
        u'comment.edit': [advisor],
        u'comment.show': [anonymous],
        u'comment.view': [anonymous],
        u'delegation.create': [voter],
        u'delegation.delete': [voter],
        u'delegation.show': [anonymous],
        u'delegation.view': [anonymous],
        u'event.index_all': [anonymous],
        u'global.admin': [admins],
        u'global.member': [admins],
        u'global.message': [admins],
        u'global.organization': [organization],
        u'global.staticpage': [admins],
        u'instance.admin': [supervisor],
        u'instance.create': [admins],
        u'instance.delete': [admins],
        u'instance.index': [anonymous],
        u'instance.join': [default],
        u'instance.leave': [default],
        u'instance.news': [anonymous],
        u'instance.show': [anonymous],
        u'instance.message': [admins],
        u'milestone.create': [supervisor],
        u'milestone.delete': [supervisor],
        u'milestone.edit': [supervisor],
        u'milestone.show': [anonymous],
        u'page.create': [advisor],
        u'page.delete': [moderator],
        u'page.delete_history': [moderator],
        u'page.edit': [advisor],
        u'page.edit_head': [moderator],
        u'page.show': [anonymous],
        u'page.view': [anonymous],
        u'poll.create': [moderator],
        u'poll.delete': [moderator],
        u'poll.show': [anonymous],
        u'proposal.create': [advisor],
        u'proposal.delete': [moderator],
        u'proposal.edit': [advisor],
        u'proposal.freeze': [supervisor],
        u'proposal.show': [anonymous],
        u'proposal.view': [anonymous],
        u'static.show': [anonymous],
        u'static.show_private': [admins],
        u'tag.create': [advisor],
        u'tag.delete': [advisor],
        u'tag.show': [anonymous],
        u'tag.view': [anonymous],
        u'user.edit': [default],
        u'user.index_all': [admins],
        u'user.manage': [admins],
        u'user.message': [advisor],
        u'user.show': [anonymous],
        u'user.view': [anonymous],
        u'vote.cast': [voter],
        u'vote.prohibit': [organization],
        u'watch.create': [observer, default],
        u'watch.delete': [observer],
        u'watch.instance': [moderator],
        u'watch.show': [anonymous],
    }

    autoupdate = asbool(config.get('adhocracy.autoassign_permissions', 'true'))
    assign_perms = initial_setup or autoupdate

    for perm_name, groups in default_permission_groups.items():
        new_perm = mk_perm(perm_name)
        if assign_perms and new_perm is not None:
            assigned_groups = included_groups(groups)
            log.debug("Assigning to groups: %s" % assigned_groups)
            new_perm.groups = assigned_groups

    model.meta.Session.commit()

    admin = model.User.find(u"admin")
    if not admin:
        email = u'admin@%s' % get_domain_part(config.get('adhocracy.domain'))
        admin = model.User.create(ADMIN, email,
                                  password=ADMIN_PASSWORD,
                                  global_admin=True)
        admin.activation_code = None

    model.meta.Session.commit()

    if config.get('adhocracy.instance'):
        model.Instance.create(config.get('adhocracy.instance'),
                              u"Adhocracy", admin)
    else:
        if not model.Instance.find(u"test"):
            log.debug(u'Creating test instance')
            model.Instance.create(u"test", u"Test Instance", admin)

        if config_get_bool('adhocracy.use_feedback_instance', config=config):
            feedback_key = config.get('adhocracy.feedback_instance_key',
                                      u'feedback')
            feedback_label = config.get('adhocracy.feedback_instance_label',
                                        u'Feedback')
            feedback_available = model.Instance.find(feedback_key)
            if feedback_key and feedback_label and not feedback_available:
                log.debug('Creating feedback instance: %s' % feedback_label)
                fb = model.Instance.create(feedback_key, feedback_label, admin)
                fb.use_norms = False
                fb.allow_adopt = False
                fb.allow_delegate = False
                fb.hide_global_categories = True
                fb.require_valid_email = False

    if 'shibboleth' in allowed_login_types(config):
        from adhocracy.lib.auth.shibboleth import get_userbadge_mapping
        for mapping in get_userbadge_mapping(config):
            title = mapping[0]
            if model.UserBadge.find(title) is None:
                model.UserBadge.create(mapping[0], u'#000000', True, u'')

    model.meta.Session.commit()
