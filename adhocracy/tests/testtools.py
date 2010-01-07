from datetime import datetime, timedelta
import random, string, time
import adhocracy.model as model

#  These functions should all go as convenience functions on the respective models

def tt_get_admin():
    return model.User.find("admin")

def tt_get_instance():
    instance = model.Instance.find("test")
    model.filter.setup_thread(instance)
    return instance

def tt_make_str(length=20):
    return u''.join([random.choice(string.letters) for i in range(length)]) 

def tt_make_motion(creator=None, voting=False):
    instance = tt_get_instance()
    if creator is None:
        creator = tt_make_user()
    issue = model.Issue(instance, tt_make_str(), creator)
    motion = model.Motion(instance, tt_make_str(), creator)
    motion.parents = [issue]
    
    if voting:
        poll = model.Poll(motion, creator)
        poll.begin_time = datetime.now() - timedelta(hours=1)
        motion.polls.append(poll)
        
    model.meta.Session.add(motion)
    print 'voting', voting
    print 'model.meta.Session.dirty', model.meta.Session.dirty
    print 'model.meta.Session.new', model.meta.Session.new
    model.meta.Session.flush()
    print 'poll', poll
    print 'motion.poll', motion.poll
    print 'motion.polls', motion.polls
    return motion

def tt_make_user(instance_group=None):
    uname = tt_make_str() 
    user = model.User(uname, u"test@test.test", u"test")
    
    default_group = model.Group.by_code(model.Group.CODE_DEFAULT)
    default_membership = model.Membership(user, None, default_group)
    memberships = [default_membership]
    
    if instance_group:
        instance = tt_get_instance()
        group_membership = model.Membership(user, instance, instance_group)
        memberships.append(group_membership)
    user.memberships = memberships 
    model.meta.Session.add(user)
    model.meta.Session.flush() # write to db and updated db generated attributes
    return user
