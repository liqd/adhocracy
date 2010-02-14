import logging
from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, UnicodeText, ForeignKey, DateTime, func
from sqlalchemy.orm import reconstructor

import meta
import filter as ifilter

log = logging.getLogger(__name__)

poll_table = Table('poll', meta.data,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', UnicodeText(), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
    )

class NoPollException(Exception): pass

class Poll(object):
    
    ADOPT = u'adopt'
    REPEAL = u'repeal'
    RATE = u'rate'
    
    ACTIONS = [ADOPT, REPEAL, RATE]
        
    def __init__(self, scope, user, action, subject=None):
        self.scope = scope
        self.user = user
        if not action in self.ACTIONS:
            raise ValueError("Invalid action!")
        self.action = action
        if subject is None:
            subject = scope
        self._subject_entity = None
        self.subject = subject
    
    
    @reconstructor
    def _reconstruct(self):
        self._subject_entity = None
    
    
    def _get_subject(self):
        import refs
        if self._subject_entity is None:
            self._subject_entity = refs.to_entity(self._subject)
        return self._subject_entity
    
    
    def _set_subject(self, subject):
        import refs
        self._subject_entity = subject
        self._subject = refs.to_ref(subject)
    
    subject = property(_get_subject, _set_subject)
    
    
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
    
    
    def can_end(self):
        if self.has_ended():
            return False
        if self.action == self.RATE:
            return False
        return True
    
    
    @classmethod
    def create(cls, scope, user, action, subject=None, with_vote=False):
        from tally import Tally
        from vote import Vote
        from adhocracy.lib.democracy import Decision
        poll = Poll(scope, user, action, subject=subject)
        meta.Session.add(poll)
        decision = Decision(user, poll)
        decision.make(Vote.YES)
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
                poll = poll.scope.instance == ifilter.get_instance() \
                        and poll or None
            return poll
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None
    
    
    def _index_id(self):
        return self.id
    
        
    def __repr__(self):
        return u"<Poll(%s,%s,%s,%s)>" % (self.id, 
                                         self.scope_id,
                                         self.begin_time, 
                                         self.end_time)
    

