from datetime import datetime
import logging

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

from meta import Base
import meta
import filter as ifilter

from vote import Vote
from poll import Poll

log = logging.getLogger(__name__)

class Tally(Base):
    __tablename__ = 'tally'
    
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    
    poll_id = Column(Integer, ForeignKey('poll.id'), nullable=False)
    poll = relation(Poll, backref=backref('tallies', order_by='Tally.create_time.desc()'))
    
    vote_id = Column(Integer, ForeignKey('vote.id'), nullable=True)
    vote = relation(Vote, backref=backref('tally', uselist=False))
    
    num_for = Column(Integer, nullable=True)
    num_against = Column(Integer, nullable=True)
    num_abstain = Column(Integer, nullable=True)
    
    def __init__(self, poll, num_for, num_against, num_abstain):
        self.poll = poll
        self.num_for = num_for
        self.num_against = num_against
        self.num_abstain = num_abstain
    
    def _get_rel_base(self):
        return self.num_for + self.num_against

    rel_base = property(_get_rel_base)
    
    def _get_rel_for(self):
        if self.rel_base == 0:
            return 0.5
        return self.num_for / float(max(1, self.rel_base))
    
    rel_for = property(_get_rel_for)
    
    def _get_rel_against(self):
        return 1 - self.rel_for
    
    rel_against = property(_get_rel_against)
    
    
    @classmethod
    def create_from_vote(cls, vote):
        tally = Tally.create_from_poll(vote.poll, vote.create_time)
        tally.vote = vote
        meta.Session.flush()
        return tally 
    
    @classmethod
    def create_from_poll(cls, poll, at_time=None):
        from adhocracy.lib.democracy import Decision
        if at_time is None:
            at_time = datetime.utcnow()
        results = {}
        for decision in Decision.for_poll(poll, at_time=at_time):
            if decision.is_decided():
                results[decision.result] = results.get(decision.result, 0) + 1
        tally = Tally(poll,
                      results.get(Vote.YES, 0), 
                      results.get(Vote.NO, 0),
                      results.get(Vote.ABSTAIN, 0))
        tally.create_time = at_time
        meta.Session.add(tally)
        meta.Session.flush()
        return tally 
    
    @classmethod
    def find_by_vote(cls, vote):
        q = meta.Session.query(Tally)
        q = q.filter(Tally.vote==vote)
        return q.limit(1).first()
    
    @classmethod
    def find_by_poll_and_time(cls, poll, time):
        q = meta.Session.query(Tally)
        q = q.filter(Tally.poll==poll)
        q = q.filter(Tally.create_time<=time)
        q = q.order_by(Tally.create_time.desc())
        return q.limit(1).first()
    
    @classmethod
    def poll_by_interval(cls, poll, from_time, to_time):
        q = meta.Session.query(Tally)
        q = q.filter(Tally.poll==poll)
        q = q.filter(Tally.create_time>=from_time)
        q = q.filter(Tally.create_time<=to_time)
        q = q.order_by(Tally.create_time.desc())
        return q.all()
      
    def __repr__(self):
        return "<Tally(%s,%s,%s,%d,%d,%d)>" % (self.id,
                                            self.poll_id,
                                            self.vote_id,
                                            self.num_for,
                                            self.num_against,
                                            self.num_abstain)
    
    def __len__(self):
        return self.num_for + self.num_against + self.num_abstain
    
    def to_dict(self):
        return dict(id=self.id,
                    poll=self.poll_id,
                    num_for=self.num_for,
                    num_against=self.num_against,
                    num_abstain=self.num_abstain)
    
    def _index_id(self):
        return self.id