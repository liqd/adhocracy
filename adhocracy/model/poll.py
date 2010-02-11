import logging
from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, DateTime, func

import meta
import filter as ifilter

log = logging.getLogger(__name__)

poll_table = Table('poll', meta.data,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('begin_user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)   
    )

class NoPollException(Exception): pass

class Poll(object):
    
    def __init__(self, proposal, begin_user):
        self.proposal = proposal
        self.begin_user = begin_user
    
    def _index_id(self):
        return self.id
    
    def end(self, end_time=None):
        if end_time is None:
            end_time = datetime.utcnow()
        if not self.has_ended(at_time=end_time):
            self.end_time = end_time
            
    def has_ended(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        
        return (self.end_time is not None) \
               and self.end_time<=at_time
            
    def delete(self, delete_time=None):
        return self.end(end_time=delete_time)
    
    def is_deleted(self, at_time=None):
        return has_ended(at_time=at_time)
    
    
    @classmethod
    def create(cls, proposal, user):
        from tally import Tally
        poll = Poll(proposal, user)
        meta.Session.add(poll)
        Tally.create_from_poll(poll)
        meta.Session.flush()
        return poll
    
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=True):
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.id==int(id))
            if not include_deleted:
                q = q.filter(or_(Poll.end_time==None,
                                 Poll.end_time>datetime.utcnow()))
            poll = q.limit(1).first()
            if ifilter.has_instance() and instance_filter and poll:
                poll = poll.proposal.instance == ifilter.get_instance() \
                        and poll or None
            return poll
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None
    
        
    def __repr__(self):
        return u"<Poll(%s,%s,%s,%s)>" % (self.id, 
                                         self.proposal_id,
                                         self.begin_time, 
                                         self.end_time)
    

