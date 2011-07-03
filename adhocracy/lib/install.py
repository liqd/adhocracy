import logging

import adhocracy.model as model

log = logging.getLogger(__name__)


def mk_group(name, code):
    group = model.Group.by_code(unicode(code))
    if not group:
        log.debug("Creating group: %s" % name)
        group = model.Group(unicode(name), unicode(code))
        model.meta.Session.add(group)
    else:
        group.group_name = unicode(name)
    return group


def mk_perm(name, *groups):
    perm = model.Permission.find(name)
    if perm is None:
        log.debug("Creating permission: %s" % name)
        perm = model.Permission(name)
        model.meta.Session.add(perm)
    perm.groups = list(groups)
    return perm


def setup_entities():
    #model.meta.Session.begin()
    model.meta.Session.commit()

    admins = mk_group("Administrator", model.Group.CODE_ADMIN)
    organization = mk_group("Organization", model.Group.CODE_ORGANIZATION)
    supervisor = mk_group("Supervisor", model.Group.CODE_SUPERVISOR)
    voter = mk_group("Voter", model.Group.CODE_VOTER)
    observer = mk_group("Observer", model.Group.CODE_OBSERVER)
    advisor = mk_group("Advisor", model.Group.CODE_ADVISOR)
    default = mk_group("Default", model.Group.CODE_DEFAULT)
    anonymous = mk_group("Anonymous", model.Group.CODE_ANONYMOUS)

    model.meta.Session.commit()

    # ADD EACH NEW PERMISSION HERE
    mk_perm("vote.cast", voter)
    mk_perm("vote.prohibit", organization)
    mk_perm("instance.index", anonymous)
    mk_perm("instance.show", anonymous)
    mk_perm("instance.create", admins)
    mk_perm("instance.admin", supervisor)
    mk_perm("instance.join", default)
    mk_perm("instance.leave", default)
    mk_perm("instance.news", anonymous)
    mk_perm("instance.delete", admins)
    mk_perm("comment.view", anonymous)
    mk_perm("comment.show", anonymous)
    mk_perm("comment.create", advisor)
    mk_perm("comment.edit", advisor)
    mk_perm("comment.delete", supervisor)
    mk_perm("proposal.create", advisor)
    mk_perm("proposal.edit", advisor)
    mk_perm("proposal.delete", supervisor)
    mk_perm("proposal.view", anonymous)
    mk_perm("proposal.show", anonymous)
    mk_perm("poll.show", anonymous)
    mk_perm("poll.create", supervisor)
    mk_perm("poll.delete", supervisor)
    mk_perm("user.manage", admins)
    mk_perm("user.edit", default)
    mk_perm("user.view", anonymous)
    mk_perm("user.show", anonymous)
    mk_perm("user.message", advisor)
    mk_perm("delegation.view", anonymous)
    mk_perm("delegation.show", anonymous)
    mk_perm("delegation.create", voter)
    mk_perm("delegation.delete", voter)
    mk_perm("watch.show", anonymous)
    mk_perm("watch.create", advisor)
    mk_perm("watch.delete", advisor)
    mk_perm("tag.show", anonymous)
    mk_perm("tag.view", anonymous)
    mk_perm("tag.create", advisor)
    mk_perm("tag.delete", advisor)
    mk_perm("page.show", anonymous)
    mk_perm("page.view", anonymous)
    mk_perm("page.create", advisor)
    mk_perm("page.edit", advisor)
    mk_perm("page.delete", supervisor)
    mk_perm("milestone.show", anonymous)
    mk_perm("milestone.create", supervisor)
    mk_perm("milestone.edit", supervisor)
    mk_perm("milestone.delete", supervisor)
    mk_perm("global.admin", admins)
    mk_perm("global.member", admins)
    mk_perm("global.organization", organization)

    model.meta.Session.commit()
    # END PERMISSIONS LIST

    advisor.permissions = advisor.permissions + anonymous.permissions
    observer.permissions = observer.permissions + advisor.permissions
    voter.permissions = voter.permissions + observer.permissions
    supervisor.permissions = supervisor.permissions + voter.permissions
    admins.permissions = admins.permissions + supervisor.permissions
    organization.permissions = observer.permissions

    admin = model.User.find(u"admin")
    if not admin:
        admin = model.User.create(u"admin", u"admin@adhocracy.de",
                                  password=u"password",
                                  global_admin=True)

    model.meta.Session.commit()

    from pylons import config
    if config.get('adhocracy.instance'):
        model.Instance.create(config.get('adhocracy.instance'),
                              u"Adhocracy", admin)
    elif not model.Instance.find(u"test"):
        model.Instance.create(u"test", u"Test Instance", admin)

    model.meta.Session.commit()
