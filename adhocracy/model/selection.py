from datetime import datetime
import logging
import simplejson as json

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import reconstructor

import meta

log = logging.getLogger(__name__)

selection_table = Table('selection', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=True)
    )

class Selection(object):
    
    def __init__(self, page, proposal):
        self.page = page
        self.proposal = proposal
        self._polls = None
    
    
    @reconstructor
    def _reconstruct(self):
        self._polls = None
    
        
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Selection)
            q = q.filter(Selection.id==id)
            if not include_deleted:
                q = q.filter(or_(Selection.delete_time==None,
                                 Selection.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.join(Proposal)
                q = q.filter(Proposal.instance==ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
    
    
    @classmethod
    def by_page(cls, page):
        try:
            q = meta.Session.query(Selection)
            q = q.filter(Selection.page==page)
            q = q.filter(or_(Selection.delete_time==None,
                             Selection.delete_time>datetime.utcnow()))
            return q.all()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
            
    
    @classmethod
    def create(cls, proposal, page, user):
        selection = Selection(page, proposal)
        meta.Session.add(selection)
        meta.Session.flush()
        for variant in page.variants: 
            selection.make_variant_poll(variant, user)
        return selection
    
    
    def make_variant_poll(self, variant, user):
        from poll import Poll
        key = self.variant_key(variant)
        for poll in self.polls:
            if poll.subject == key:
                return poll
        poll = Poll.create(self.page, user, Poll.SELECT, 
                           subject=key)
        if self._polls is not None:
            self._polls.append(poll)
        return poll
    
    
    def variant_key(self, variant):
        return "[@[selection:%d],\"%s\"]" % (self.id, variant)
    
    
    @property
    def subjects(self):
        return [self.variant_key(v) for v in self.page.variants]
        
    
    @property
    def polls(self):
        from poll import Poll
        if self._polls is None:
            self._polls = Poll.by_subjects(self.subjects)
        return self._polls
    
    
    def to_dict(self):
        d = dict(id=self.id,
                 create_time=self.create_time,
                 page=self.page.id,
                 proposal=self.proposal.id)
        return d
    
            
    def _index_id(self):
        return self.id
    
    
    def __repr__(self):
        return u"<Selection(%d,%s,%s)>" % (self.id, self.page.id, 
                                           self.proposal.id if self.proposal else "-")

    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
