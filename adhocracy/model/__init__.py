"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm

from adhocracy.model.user import User
from adhocracy.model.openid import OpenID
from adhocracy.model.twitter import Twitter
from adhocracy.model.group import Group
from adhocracy.model.permission import Permission
from adhocracy.model.delegateable import Delegateable
from adhocracy.model.issue import Issue
from adhocracy.model.delegation import Delegation
from adhocracy.model.proposal import Proposal
from adhocracy.model.poll import Poll
from adhocracy.model.vote import Vote
from adhocracy.model.revision import Revision
from adhocracy.model.comment import Comment
from adhocracy.model.instance import Instance
from adhocracy.model.membership import Membership
from adhocracy.model.karma import Karma
from adhocracy.model.alternative import Alternative
from adhocracy.model.dependency import Dependency
from adhocracy.model.watch import Watch
from adhocracy.model.event import Event

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    sm = orm.sessionmaker(autoflush=True, bind=engine)
    meta.engine = engine
    meta.Session = orm.scoped_session(sm)
    
    #import adhocracy.lib.search as search
    #search.rebuild_all()
    
        


