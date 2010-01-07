from datetime import datetime, timedelta
import random, string, time
import adhocracy.model as model
import adhocracy.lib.instance as libinstance

#  These functions should all go as convenience functions on the respective models

def tt_get_admin():
    admin = model.User(tt_make_str(), u"admin@null.naught", u"password")
    model.meta.Session.add(admin)     
    model.meta.Session.flush()
    return admin

def tt_get_instance():
    instance = model.Instance.find(u"test")
    if not instance:
        instance = model.Instance(u"test", u"foo schnasel", tt_make_user())
        model.meta.Session.add(instance)
        model.meta.Session.flush()
    model.filter.setup_thread(instance)
    return instance

def tt_make_str(length=20):
    return u''.join([random.choice(string.letters) for i in range(length)]) 

def tt_make_proposal(creator=None, voting=False):
    instance = tt_get_instance()
    if creator is None:
        creator = tt_make_user()
    issue = model.Issue(instance, tt_make_str(), creator)
    proposal = model.Proposal(instance, tt_make_str(), creator)
    proposal.parents = [issue]
    
    if voting:
        poll = model.Poll(proposal, creator)
        poll.begin_time = datetime.utcnow() - timedelta(hours=1)
        proposal.polls.append(poll)
        
    model.meta.Session.add(proposal)
    model.meta.Session.flush()
    return proposal

def tt_make_user(instance_group=None):
    uname = tt_make_str() 
    user = model.User(uname, u"test@test.test", u"test")
    
    #default_group = model.Group.by_code(model.Group.CODE_DEFAULT)
    #default_membership = model.Membership(user, None, default_group)
    #memberships = [default_membership]
    
    #if instance_group:
    #    instance = tt_get_instance()
    #    group_membership = model.Membership(user, instance, instance_group)
    #    memberships.append(group_membership)
    #user.memberships = memberships 
    model.meta.Session.add(user)
    model.meta.Session.flush() # write to db and updated db generated attributes
    return user
