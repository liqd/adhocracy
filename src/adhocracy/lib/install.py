import logging

import adhocracy.model as model

from pylons import config
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


def mk_perm(name, set_groups, *groups):
    perm = model.Permission.find(name)
    if perm is None:
        log.debug("Creating permission: %s" % name)
        perm = model.Permission(name)
        model.meta.Session.add(perm)
    if set_groups:
        perm.groups = list(groups)
    return perm


def setup_entities(initial_setup):
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

    # ADD EACH NEW PERMISSION HERE
    mk_perm("comment.create", initial_setup, advisor)
    mk_perm("comment.delete", initial_setup, moderator)
    mk_perm("comment.edit", initial_setup, advisor)
    mk_perm("comment.show", initial_setup, anonymous)
    mk_perm("comment.view", initial_setup, anonymous)
    mk_perm("delegation.create", initial_setup, voter)
    mk_perm("delegation.delete", initial_setup, voter)
    mk_perm("delegation.show", initial_setup, anonymous)
    mk_perm("delegation.view", initial_setup, anonymous)
    mk_perm("global.admin", initial_setup, admins)
    mk_perm("global.member", initial_setup, admins)
    mk_perm("global.message", initial_setup, admins)
    mk_perm("global.organization", initial_setup, organization)
    mk_perm("instance.admin", initial_setup, supervisor)
    mk_perm("instance.create", initial_setup, admins)
    mk_perm("instance.delete", initial_setup, admins)
    mk_perm("instance.index", initial_setup, anonymous)
    mk_perm("instance.join", initial_setup, default)
    mk_perm("instance.leave", initial_setup, default)
    mk_perm("instance.news", initial_setup, anonymous)
    mk_perm("instance.show", initial_setup, anonymous)
    mk_perm("instance.message", initial_setup, admins)
    mk_perm("milestone.create", initial_setup, supervisor)
    mk_perm("milestone.delete", initial_setup, supervisor)
    mk_perm("milestone.edit", initial_setup, supervisor)
    mk_perm("milestone.show", initial_setup, anonymous)
    mk_perm("page.create", initial_setup, advisor)
    mk_perm("page.delete", initial_setup, moderator)
    mk_perm("page.delete_history", initial_setup, moderator)
    mk_perm("page.edit", initial_setup, advisor)
    mk_perm("page.show", initial_setup, anonymous)
    mk_perm("page.view", initial_setup, anonymous)
    mk_perm("poll.create", initial_setup, moderator)
    mk_perm("poll.delete", initial_setup, moderator)
    mk_perm("poll.show", initial_setup, anonymous)
    mk_perm("proposal.create", initial_setup, advisor)
    mk_perm("proposal.delete", initial_setup, moderator)
    mk_perm("proposal.edit", initial_setup, advisor)
    mk_perm("proposal.show", initial_setup, anonymous)
    mk_perm("proposal.view", initial_setup, anonymous)
    mk_perm("tag.create", initial_setup, advisor)
    mk_perm("tag.delete", initial_setup, advisor)
    mk_perm("tag.show", initial_setup, anonymous)
    mk_perm("tag.view", initial_setup, anonymous)
    mk_perm("user.edit", initial_setup, default)
    mk_perm("user.manage", initial_setup, admins)
    mk_perm("user.message", initial_setup, advisor)
    mk_perm("user.show", initial_setup, anonymous)
    mk_perm("user.view", initial_setup, anonymous)
    mk_perm("vote.cast", initial_setup, voter)
    mk_perm("vote.prohibit", initial_setup, organization)
    mk_perm("watch.create", initial_setup, observer)
    mk_perm("watch.delete", initial_setup, observer)
    mk_perm("watch.show", initial_setup, anonymous)

    model.meta.Session.commit()
    # END PERMISSIONS LIST

    if initial_setup:

        observer.permissions = observer.permissions + anonymous.permissions
        advisor.permissions = advisor.permissions + observer.permissions
        voter.permissions = voter.permissions + advisor.permissions
        moderator.permissions = moderator.permissions + voter.permissions
        supervisor.permissions = list(set(supervisor.permissions
                                          + moderator.permissions
                                          + advisor.permissions))
        admins.permissions = admins.permissions + supervisor.permissions
        organization.permissions = list(set(organization.permissions
                                            + observer.permissions))
        addressee.permissions = voter.permissions

    admin = model.User.find(u"admin")
    if not admin:
        admin = model.User.create(ADMIN, u'',
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

        if asbool(config.get('adhocracy.use_feedback_instance')):
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

    model.meta.Session.commit()
