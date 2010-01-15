import logging
from datetime import datetime

from sqlalchemy import Column, Unicode, ForeignKey, Integer, or_
from sqlalchemy.orm import relation

import meta
import filter

from delegateable import Delegateable

log = logging.getLogger(__name__)

# REFACT: rename to Proposal to make it more clear that this is a concrete proposition
# Might even go as far and call them Solutions (nice symetry between Issues and Solutions)
class Proposal(Delegateable):
    __tablename__ = 'proposal'
    __mapper_args__ = {'polymorphic_identity': 'proposal'}
    
    id = Column(Integer, ForeignKey('delegateable.id'), primary_key=True)
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=True)
              
    def __init__(self, instance, label, creator):
        self.init_child(instance, label, creator)
        
    def __repr__(self):
        return u"<Proposal(%s)>" % self.id
    
    def _get_issue(self):
        if len(self.parents) != 1:
            raise ValueError(_("Proposal doesn't have a distinct parent issue."))
        return self.parents[0]
    
    def _set_issue(self, issue):
        self.parents = [issue]

    issue = property(_get_issue, _set_issue)
    
    def _get_poll(self):
        for poll in self.polls:
            if not poll.end_time:
                return poll
        return None
    
    poll = property(_get_poll)
    
    def search_children(self, recurse=False, cls=Delegateable):
        return []
    
    def poll_at(self, at_time):
        for poll in self.polls:
            if poll.begin_time > at_time:
                continue
            if poll.end_time and poll.end_time < at_time:
                continue
            return poll
        return None
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Proposal)
            q = q.filter(Proposal.id==int(id))
            if not include_deleted:
                q = q.filter(or_(Proposal.delete_time==None,
                                 Proposal.delete_time>datetime.utcnow()))
            if filter.has_instance() and instance_filter:
                q = q.filter(Proposal.instance_id==filter.get_instance().id)
            return q.one()
        except: 
            log.exception("find(%s)" % id)
            return None
    
    @classmethod    
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Proposal)
        if not include_deleted:
            q = q.filter(or_(Proposal.delete_time==None,
                             Proposal.delete_time>datetime.utcnow()))
        if instance is not None:
            q = q.filter(Proposal.instance==instance)
        return q.all()
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        super(Proposal, self).delete(delete_time=delete_time)
        for alternative in self.left_alternatives:
            alternative.delete(delete_time=delete_time)
        for alternative in self.right_alternatives:
            alternative.delete(delete_time=delete_time)
        for dependency in self.dependencies:
            dependency.delete(delete_time=delete_time)
        for dependency in self.dependents:
            dependency.delete(delete_time=delete_time)
        # TODO: This really SHOULD have some check: 
        for poll in self.polls:
            poll.delete()
    

Proposal.comment = relation('Comment', 
                          primaryjoin="Proposal.comment_id==Comment.id", 
                          foreign_keys=[Proposal.comment_id], 
                          uselist=False)