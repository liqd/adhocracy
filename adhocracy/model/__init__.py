"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm

# REFACT: remove the subpackage imports - as they serve no purpose right now (the class imports are what we really want to keep)

from adhocracy.model import meta

from adhocracy.model import user
from adhocracy.model.user import User

from adhocracy.model import openid
from adhocracy.model.openid import OpenID

from adhocracy.model import twitter
from adhocracy.model.twitter import Twitter

from adhocracy.model import group
from adhocracy.model.group import Group

from adhocracy.model import permission
from adhocracy.model.permission import Permission

from adhocracy.model import delegateable
from adhocracy.model.delegateable import Delegateable

from adhocracy.model import issue
from adhocracy.model.issue import Issue

from adhocracy.model import delegation
from adhocracy.model.delegation import Delegation

from adhocracy.model import motion
from adhocracy.model.motion import Motion

from adhocracy.model import poll
from adhocracy.model.poll import Poll

from adhocracy.model import vote
from adhocracy.model.vote import Vote

from adhocracy.model import revision
from adhocracy.model.revision import Revision

from adhocracy.model import comment
from adhocracy.model.comment import Comment

from adhocracy.model import instance
from adhocracy.model.instance import Instance

from adhocracy.model import membership
from adhocracy.model.membership import Membership

from adhocracy.model import karma
from adhocracy.model.karma import Karma

from adhocracy.model import alternative
from adhocracy.model.alternative import Alternative

from adhocracy.model import dependency
from adhocracy.model.dependency import Dependency

from adhocracy.model import watch
from adhocracy.model.watch import Watch

from adhocracy.model import event
from adhocracy.model.event import Event

from adhocracy.model import filter
from adhocracy.model import refs

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    sm = orm.sessionmaker(autoflush=True, bind=engine)
    meta.engine = engine
    meta.Session = orm.scoped_session(sm)
    
    #import adhocracy.lib.search as search
    #search.rebuild_all()
    
        


