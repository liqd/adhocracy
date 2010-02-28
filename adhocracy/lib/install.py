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
    supervisor = mk_group("Supervisor", model.Group.CODE_SUPERVISOR)
    voter = mk_group("Voter", model.Group.CODE_VOTER)
    observer = mk_group("Observer", model.Group.CODE_OBSERVER)
    default = mk_group("Default", model.Group.CODE_DEFAULT)
    anonymous = mk_group("Anonymous", model.Group.CODE_ANONYMOUS)
    
    model.meta.Session.commit()
    
    # ADD EACH NEW PERMISSION HERE
    mk_perm("vote.cast", voter)
    mk_perm("karma.give", voter)
    mk_perm("instance.index", anonymous)
    mk_perm("instance.view", anonymous)
    mk_perm("instance.create", default)
    mk_perm("instance.admin", supervisor)
    mk_perm("instance.join", default)
    mk_perm("instance.leave", default)
    mk_perm("instance.news", anonymous)
    mk_perm("instance.delete", admins)
    mk_perm("comment.view", anonymous)
    mk_perm("comment.create", observer)
    mk_perm("comment.edit", observer)
    mk_perm("comment.delete", supervisor)
    mk_perm("proposal.create", observer)
    mk_perm("proposal.edit", observer)
    mk_perm("proposal.delete", supervisor)
    mk_perm("proposal.view", anonymous)
    mk_perm("poll.create", voter)
    mk_perm("poll.delete", supervisor)
    mk_perm("issue.create", observer)
    mk_perm("issue.edit", observer)
    mk_perm("issue.delete", supervisor)
    mk_perm("issue.view", anonymous)
    mk_perm("user.manage", admins)
    mk_perm("user.edit", default)
    mk_perm("user.view", anonymous)
    mk_perm("delegation.view", anonymous)
    mk_perm("watch.create", observer)
    mk_perm("watch.delete", observer)
    mk_perm("tag.view", anonymous)
    mk_perm("tag.create", observer)
    mk_perm("tag.delete", observer)
    mk_perm("global.admin", admins)
    mk_perm("global.member", admins)
    
    model.meta.Session.commit()
    # END PERMISSIONS LIST
        
    observer.permissions = observer.permissions + anonymous.permissions
    voter.permissions = voter.permissions + observer.permissions
    supervisor.permissions = supervisor.permissions + voter.permissions
    admins.permissions = admins.permissions + supervisor.permissions
    
    
    admin = model.User.find(u"admin")
    if not admin:
        admin = model.User.create(u"admin", u"admin@null.naught", 
                                  password=u"password", 
                                  global_admin=True)  
        
    model.meta.Session.commit()
    
    import instance as libinstance
    if not model.Instance.find(u"test"):
        model.Instance.create(u"test", u"Test Instance", admin)
