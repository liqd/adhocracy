"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import mapper, relation, backref, synonym

import meta

from adhocracy.model.user import User, user_table
from adhocracy.model.openid import OpenID, openid_table
from adhocracy.model.twitter import Twitter, twitter_table
from adhocracy.model.group import Group, group_table
from adhocracy.model.permission import Permission, group_permission_table, permission_table
from adhocracy.model.delegateable import Delegateable, delegateable_table, category_graph
from adhocracy.model.issue import Issue, issue_table
from adhocracy.model.delegation import Delegation, delegation_table
from adhocracy.model.proposal import Proposal, proposal_table
from adhocracy.model.alternative import Alternative, alternative_table
from adhocracy.model.dependency import Dependency, dependency_table
from adhocracy.model.poll import Poll, poll_table
from adhocracy.model.vote import Vote, vote_table
from adhocracy.model.revision import Revision, revision_table
from adhocracy.model.comment import Comment, comment_table
from adhocracy.model.instance import Instance, instance_table
from adhocracy.model.membership import Membership, membership_table
from adhocracy.model.karma import Karma, karma_table
from adhocracy.model.watch import Watch, watch_table
from adhocracy.model.event import Event, event_topic_table, event_table
from adhocracy.model.tally import Tally, tally_table


mapper(User, user_table, properties={
    'email': synonym('_email', map_column=True),
    'locale': synonym('_locale', map_column=True),
    'password': synonym('_password', map_column=True)
    }, extension=meta.extension)


mapper(Twitter, twitter_table, properties={
    'user': relation(User, lazy=False, primaryjoin=twitter_table.c.user_id==user_table.c.id, 
                     backref=backref('twitters', cascade='delete'))
    }, extension=meta.extension)


mapper(OpenID, openid_table, properties={
    'user': relation(User, lazy=False, primaryjoin=openid_table.c.user_id==user_table.c.id, 
                     backref=backref('openids', cascade='delete'))
    }, extension=meta.extension)


mapper(Group, group_table, extension=meta.extension)


mapper(Permission, permission_table, properties={
    'groups': relation(Group, secondary=group_permission_table, lazy=False,
                       backref=backref('permissions', lazy=False))
    }, extension=meta.extension)


mapper(Delegateable, delegateable_table, polymorphic_on=delegateable_table.c.type, properties={
    'parents': relation(Delegateable, lazy=True, secondary=category_graph, 
                        primaryjoin=delegateable_table.c.id == category_graph.c.parent_id,
                        secondaryjoin=category_graph.c.child_id == delegateable_table.c.id),
    'children': relation(Delegateable, lazy=True, secondary=category_graph, 
                         primaryjoin=delegateable_table.c.id == category_graph.c.child_id,
                         secondaryjoin=category_graph.c.parent_id == delegateable_table.c.id),
    'creator': relation(User, primaryjoin=delegateable_table.c.creator_id==user_table.c.id, 
                        backref=backref('delegateables', cascade='delete')),
    'instance': relation(Instance, lazy=True,
                        primaryjoin=delegateable_table.c.instance_id==instance_table.c.id, 
                        backref=backref('delegateables', cascade='delete'))
    }, extension=meta.extension)


mapper(Issue, issue_table, inherits=Delegateable, polymorphic_identity='issue', properties={
    'comment': relation(Comment, primaryjoin=issue_table.c.comment_id==comment_table.c.id, 
                        uselist=False)
    }, extension=meta.extension)


mapper(Proposal, proposal_table, inherits=Delegateable, polymorphic_identity='proposal', properties={
    'comment': relation(Comment, primaryjoin=proposal_table.c.comment_id==comment_table.c.id, 
                        uselist=False)
    }, extension=meta.extension)


mapper(Alternative, alternative_table, properties={
    'left': relation(Proposal, primaryjoin=alternative_table.c.left_id==proposal_table.c.id,  
                     backref=backref('left_alternatives', cascade='all')),
    'right': relation(Proposal, primaryjoin=alternative_table.c.right_id==proposal_table.c.id, 
                      backref=backref('right_alternatives', cascade='all'))
    }, extension=meta.extension)


mapper(Comment, comment_table, properties={
    'latest': relation(Revision, primaryjoin=revision_table.c.comment_id==comment_table.c.id,
                       order_by=revision_table.c.create_time.desc(), uselist=False,
                       viewonly=True, lazy=False),
    'creator': relation(User, lazy=False, backref=backref('comments')),
    'topic': relation(Delegateable, backref=backref('comments', cascade='all')),
    'reply': relation(Comment, cascade='delete', remote_side=comment_table.c.id, 
                      backref=backref('replies', lazy=True))
    }, extension=meta.extension)


mapper(Revision, revision_table, properties={
    'user': relation(User, lazy=True, primaryjoin=revision_table.c.user_id==user_table.c.id, 
                     backref=backref('revisions', cascade='all')),
    'comment': relation(Comment, lazy=False, backref=backref('revisions', cascade='all',
                        lazy=True, order_by=revision_table.c.create_time.desc()))
    }, extension=meta.extension)
    

mapper(Delegation, delegation_table, properties={
    'agent': relation(User, primaryjoin=delegation_table.c.agent_id==user_table.c.id, 
                      backref=backref('agencies', cascade='all')),
    'principal': relation(User, primaryjoin=delegation_table.c.principal_id==user_table.c.id, 
                          backref=backref('delegated', cascade='all')),
    'scope': relation(Delegateable, lazy=False, primaryjoin=delegation_table.c.scope_id==delegateable_table.c.id, 
                      backref=backref('delegations', cascade='all'))                                             
    }, extension=meta.extension)


mapper(Dependency, dependency_table, properties={
    'proposal': relation(Proposal, primaryjoin=dependency_table.c.proposal_id==proposal_table.c.id,  
                         backref=backref('dependencies', cascade='all')),
    'requirement': relation(Proposal, primaryjoin=dependency_table.c.requirement_id==proposal_table.c.id, 
                            backref=backref('dependents', cascade='all'))
    }, extension=meta.extension)


mapper(Poll, poll_table, properties={
    'begin_user': relation(User, primaryjoin=poll_table.c.begin_user_id==user_table.c.id),
    'proposal': relation(Proposal, backref=backref('polls', cascade='all',
                         lazy=False, order_by=poll_table.c.begin_time.desc())),
    'tally': relation(Tally, primaryjoin=tally_table.c.poll_id==poll_table.c.id,
                      order_by=tally_table.c.create_time.desc(), uselist=False,
                      viewonly=True, lazy=False)
    }, extension=meta.extension)


mapper(Vote, vote_table, properties={
    'user': relation(User, primaryjoin=vote_table.c.user_id==user_table.c.id, 
                     backref=backref('votes', cascade='delete', order_by='Vote.create_time.desc()')),
    'poll': relation(Poll, backref=backref('votes', order_by=vote_table.c.create_time.desc())),
    'delegation': relation(Delegation, primaryjoin=vote_table.c.delegation_id==delegation_table.c.id, 
                           backref=backref('votes', cascade='delete'))
    }, extension=meta.extension)


mapper(Instance, instance_table, properties={
    'creator': relation(User, primaryjoin=instance_table.c.creator_id==user_table.c.id, 
                        backref=backref('created_instances')),
    'default_group': relation(Group, lazy=True)
    }, extension=meta.extension)


mapper(Membership, membership_table, properties={
    'user': relation(User, lazy=False, primaryjoin=membership_table.c.user_id==user_table.c.id, 
                    backref=backref('memberships', lazy=True)),
    'instance': relation(Instance, backref=backref('memberships'), lazy=True),
    'group': relation(Group, backref=backref('memberships'), lazy=False)
    }, extension=meta.extension)


mapper(Karma, karma_table, properties={
    'comment': relation(Comment, backref=backref('karmas', cascade='delete')),
    'donor': relation(User, primaryjoin=karma_table.c.donor_id==user_table.c.id,
                     backref=backref('karma_given')),
    'recipient': relation(User, primaryjoin=karma_table.c.recipient_id==user_table.c.id,
                         backref=backref('karma_received'))
    }, extension=meta.extension)


mapper(Watch, watch_table, properties={
    'user': relation(User, primaryjoin=watch_table.c.user_id==user_table.c.id)
    }, extension=meta.extension)


mapper(Event, event_table, properties={
    'data': synonym('_data', map_column=True),
    'event': synonym('_event', map_column=True),
    'user': relation(User, lazy=False, primaryjoin=event_table.c.user_id==user_table.c.id),
    'instance': relation(Instance, lazy=True, primaryjoin=event_table.c.instance_id==instance_table.c.id),
    'topics': relation(Delegateable, secondary=event_topic_table, lazy=True)
    }, extension=meta.extension)


mapper(Tally, tally_table, properties={
    'poll': relation(Poll, backref=backref('tallies', order_by=tally_table.c.create_time.desc())),
    'vote': relation(Vote, backref=backref('tally', uselist=False))
    }, extension=meta.extension)



def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    sm = orm.sessionmaker(autoflush=True, bind=engine)
    meta.engine = engine
    meta.Session = orm.scoped_session(sm)
    
        


