from datetime import datetime, timedelta
import random, string, time
import adhocracy.model as model
import adhocracy.lib.instance as libinstance
import adhocracy.lib.text.i18n as i18n

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
    # shouldn't setup_threads instance be returned if available?
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
    model.meta.Session.add(proposal)
    model.meta.Session.flush()
    
    if voting:
        an_hour_ago = datetime.utcnow() - timedelta(hours=2)
        poll = model.Poll.create(proposal, creator, model.Poll.ADOPT)
        poll.begin_time = an_hour_ago
        proposal.polls.append(poll)
        model.meta.Session.flush()
        
    return proposal

def tt_make_user(name=None): # instance_group=None: not supported right now
    if name is not None:
        name = unicode(name)
        user = model.meta.Session.query(model.User).filter(model.User.user_name==name).first()
        if user:
            return user
    
    if name is None:
        name = tt_make_str()
    user = model.User(name, u"test@test.test", u"test", i18n.DEFAULT)
    
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
