from datetime import datetime, timedelta
import random, string, time
import adhocracy.model as model

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
    if not creator:
        creator = tt_make_user()
    issue = model.Issue(instance, tt_make_str(), creator)
    motion = model.Motion(instance, tt_make_str(), creator)
    motion.parents = [issue]
    model.meta.Session.add(motion)
    model.meta.Session.commit()
    model.meta.Session.refresh(motion)
    
    if voting:
        # should be Poll.begin_time and Poll.end_time (datetimes)
        model.poll.begin_time = datetime.now()
        # tr = model.Transition(motion, model.Motion.STATE_VOTING, creator)
        # motion.transitions.append(tr)
        # model.meta.Session.add(motion)
        # model.meta.Session.commit() 
    return motion

def tt_make_user(instance_group=None):
    uname = tt_make_str() 
    user = model.User(uname, u"test@test.test", u"test")
    
    defgrp = model.Group.by_code(model.Group.CODE_DEFAULT)
    defmembr = model.Membership(user, None, defgrp)
    memberships = [defmembr]
    model.meta.Session.add(defmembr)
    
    if instance_group:
        instance = tt_get_instance()
        grpmembr = model.Membership(user, instance, instance_group)
        model.meta.Session.add(grpmembr)
        memberships.append(grpmembr)
    user.memberships = memberships 
    model.meta.Session.add(user)
    model.meta.Session.commit()
    model.meta.Session.refresh(user)
    return user
