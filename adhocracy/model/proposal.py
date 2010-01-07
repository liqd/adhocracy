import logging

from sqlalchemy import Column, Unicode, ForeignKey, Integer
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
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Proposal)
            q = q.filter(Proposal.id==id)
            q = q.filter(Proposal.delete_time==None)
            if filter.has_instance() and instance_filter:
                q = q.filter(Proposal.instance_id==filter.get_instance().id)
            return q.one()
        except: 
            return None
    
    @classmethod    
    def all(cls, instance=None):
        q = meta.Session.query(Proposal)
        q = q.filter(Proposal.delete_time==None)
        if instance:
            q = q.filter(Proposal.instance==instance)
        return q.all()
    

Proposal.comment = relation('Comment', 
                          primaryjoin="Proposal.comment_id==Comment.id", 
                          foreign_keys=[Proposal.comment_id], 
                          uselist=False)