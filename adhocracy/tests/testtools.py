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
    
    cat = instance.root.search_children(cls=model.Category)[0]
    motion = model.Motion(instance, tt_make_str(), creator)
    motion.parents = [cat]
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

def tt_make_user(group=None):
    user = None
    while True:
        uname = tt_make_str()
        if not model.User.find(uname):
            user = model.User(uname, u"test@test.test", u"test")
            break
    defgrp = model.Group.by_code(model.Group.CODE_DEFAULT)
    defmembr = model.Membership(user, None, defgrp)
    
    instance = tt_get_instance()
    if not group:
        group = model.Group.by_code(model.Group.CODE_VOTER)
    grpmembr = model.Membership(user, instance, group) 
    model.meta.Session.add(user)
    user.memberships += [defmembr, grpmembr]
    model.meta.Session.add(defmembr)
    model.meta.Session.add(grpmembr)
    model.meta.Session.commit()
    model.meta.Session.refresh(user)
    return user
