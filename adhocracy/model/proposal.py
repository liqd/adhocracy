import logging
from itertools import chain
from datetime import datetime

from sqlalchemy import Table, Column, Unicode, ForeignKey, Integer, or_, and_
from sqlalchemy.orm import reconstructor, aliased, eagerload

import meta
import filter

from delegateable import Delegateable

log = logging.getLogger(__name__)

proposal_table = Table('proposal', meta.data,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
    Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    )

class Proposal(Delegateable):
       
    def __init__(self, instance, label, creator):
        self.init_child(instance, label, creator)
        self._current_alternatives = None
        
    
    @reconstructor
    def _reconstruct(self):
        self._current_alternatives = None
    
    
    def _get_issue(self):
        if len(self.parents) != 1:
            raise ValueError(_("Proposal doesn't have a distinct parent issue."))
        return self.parents[0]
    
    def _set_issue(self, issue):
        self.parents = [issue]

    issue = property(_get_issue, _set_issue)
        
    def search_children(self, recurse=False, cls=Delegateable):
        return []
        
    def _get_canonicals(self):
        return [c for c in self.comments if c.canonical and not c.is_deleted()]
    
    canonicals = property(_get_canonicals)
    
    def is_mutable(self):
        return self.adopt_poll is None or self.adopt_poll.has_ended()
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False, full=False):
        try:
            q = meta.Session.query(Proposal)
            q = q.filter(Proposal.id==int(id))
            if not include_deleted:
                q = q.filter(or_(Proposal.delete_time==None,
                                 Proposal.delete_time>datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None
    
    @classmethod
    def find_by_creator(cls, user, instance_filter=True):
        q = meta.Session.query(Proposal)
        q = q.filter(Proposal.creator==user)
        q = q.filter(or_(Proposal.delete_time==None,
                         Proposal.delete_time>datetime.utcnow()))
        if filter.has_instance() and instance_filter:
            q = q.filter(Proposal.instance_id==filter.get_instance().id)
        return q.all()
    
    @classmethod    
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Proposal)
        if not include_deleted:
            q = q.filter(or_(Proposal.delete_time==None,
                             Proposal.delete_time>datetime.utcnow()))
        if instance is not None:
            q = q.filter(Proposal.instance==instance)
        return q.all()
    
    @classmethod
    def create(cls, instance, label, user, issue):
        from poll import Poll
        proposal = Proposal(instance, label, user)
        proposal.issue = issue
        meta.Session.add(proposal)
        meta.Session.flush()
        poll = Poll.create(proposal, user, Poll.RATE)
        proposal.rate_poll = poll
        meta.Session.flush()
        return proposal
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        super(Proposal, self).delete(delete_time=delete_time)
        for alternative in self.left_alternatives:
            alternative.delete(delete_time=delete_time)
        for alternative in self.right_alternatives:
            alternative.delete(delete_time=delete_time)
            
    def comment_count(self):
        count = len([c for c in self.comments if not c.is_deleted()])
        if self.comment and not self.comment.is_deleted():
            count -= 1
        return count - len(self.canonicals) 
    
    def current_alternatives(self):
        if self._current_alternatives is None:
            self._current_alternatives = []
            alternatives = chain(self.left_alternatives, self.right_alternatives)
            for alternative in alternatives:
                if alternative.is_deleted():
                    continue
                self._current_alternatives.append(alternative.other(self))
        return self._current_alternatives
    
    def update_alternatives(self, alternatives):
        from alternative import Alternative
        delete_list = []
        new_list = list(alternatives)
        for alternative in chain(self.left_alternatives, self.right_alternatives):
            if alternative.is_deleted(): continue
            other = alternative.other(self)
            if other in alternatives:
                new_list.remove(other)
            else:
                delete_list.append(other)
        [a.delete() for a in delete_list]
        for proposal in new_list:
            alternative = Alternative(self, proposal)
            meta.Session.add(alternative)
    
    def __repr__(self):
        return u"<Proposal(%s)>" % self.id

