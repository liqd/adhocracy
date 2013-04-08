from datetime import datetime
import logging
from sets import Set

from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime

import meta


log = logging.getLogger(__name__)


tally_table = Table(
    'tally', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('vote_id', Integer, ForeignKey('vote.id'), nullable=True),
    Column('num_for', Integer, nullable=True),
    Column('num_against', Integer, nullable=True),
    Column('num_abstain', Integer, nullable=True)
)


class Tally(object):
    '''
    Keep track of the current the number of votes in a poll.
    There to hold denormalized data available in polls.

    TODO: Move this information to solr where we index anyway?
    '''

    def __init__(self, poll, num_for, num_against, num_abstain):
        self.poll = poll
        self.num_for = num_for
        self.num_against = num_against
        self.num_abstain = num_abstain

    def _get_rel_for(self):
        base = self.num_for + self.num_against
        if base == 0:
            return 0.5
        return self.num_for / float(max(1, base))

    rel_for = property(_get_rel_for)

    def _get_rel_against(self):
        return 1 - self.rel_for

    rel_against = property(_get_rel_against)

    def _get_score(self):
        return self.num_for - self.num_against

    score = property(_get_score)

    @classmethod
    def create_from_vote(cls, vote):
        tally = cls.find_by_vote(vote)
        if tally is None:
            tally = Tally.create_from_poll(vote.poll, vote.create_time)
            tally.vote = vote
            meta.Session.flush()
        return tally

    @classmethod
    def create_from_poll(cls, poll, at_time=None, user_filter=None):
        from adhocracy.lib.democracy.tally import make_from_poll
        tally = make_from_poll(cls, poll, at_time=at_time,
                               user_filter=user_filter)
        meta.Session.add(tally)
        meta.Session.flush()
        return tally

    @classmethod
    def combine_polls(cls, polls, at_time=None):
        from adhocracy.lib.democracy import Decision
        from vote import Vote
        if at_time is None:
            at_time = datetime.utcnow()
        voters = {Vote.YES: Set(),
                  Vote.NO: Set(),
                  Vote.ABSTAIN: Set()}

        for poll in polls:
            for decision in Decision.for_poll(poll, at_time=at_time):
                if not decision.is_decided():
                    continue
                result = decision.result
                if result is not None:
                    voters_ = voters.get(result)
                    voters_.add(decision.user)

        # Do the math. We count only non-contradictory votes.
        yes = voters[Vote.YES]
        no = voters[Vote.NO]
        abstain = voters[Vote.ABSTAIN]
        return Tally(None,
                     len(yes - no - abstain),
                     len(no - yes - abstain),
                     len(abstain - yes - no))

    @classmethod
    def find_by_vote(cls, vote):
        q = meta.Session.query(Tally)
        q = q.filter(Tally.vote == vote)
        return q.limit(1).first()

    @classmethod
    def all_samples(cls, poll, start_time, end_time):
        qp = meta.Session.query(Tally)
        qp = qp.filter(Tally.poll == poll)
        qp = qp.filter(Tally.create_time <= end_time)
        qp = qp.filter(Tally.create_time >= start_time)
        qp = qp.order_by(Tally.create_time.asc())
        qp = qp.order_by(Tally.id.asc())
        qb = meta.Session.query(Tally)
        qb = qb.filter(Tally.poll == poll)
        qb = qb.filter(Tally.create_time < start_time)
        qb = qb.order_by(Tally.create_time.desc())
        qb = qb.order_by(Tally.id.desc())
        qb = qb.limit(1)
        # TODO fix this as a union query, but that requires
        # some parantheses that SQLalchemy will not set.
        return qb.all() + qp.all()

    def has_majority(self):
        quorum = self.poll.scope.instance.required_majority
        return self.rel_for > quorum

    def has_participation(self):
        quorum = self.poll.scope.instance.required_participation
        return len(self) >= quorum

    def __len__(self):
        return self.num_for + self.num_against + self.num_abstain

    def to_dict(self):
        return dict(id=self.id,
                    poll=self.poll_id,
                    score=self.score,
                    num_for=self.num_for,
                    num_against=self.num_against,
                    num_abstain=self.num_abstain)

    def _index_id(self):
        return self.id

    def __repr__(self):
        return "<Tally(%s,%s,%s,%d,%d,%d)>" % (self.id,
                                               self.poll_id,
                                               self.vote_id,
                                               self.num_for,
                                               self.num_against,
                                               self.num_abstain)
