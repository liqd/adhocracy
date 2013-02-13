import logging
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, Unicode
from sqlalchemy.orm import reconstructor, eagerload

import meta
import instance_filter as ifilter

log = logging.getLogger(__name__)


poll_table = Table(
    'poll', meta.data,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', Unicode(254), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
)


class NoPollException(Exception):
    pass


class Poll(object):

    ADOPT = u'adopt'
    RATE = u'rate'
    SELECT = u'select'

    ACTIONS = [ADOPT, RATE, SELECT]

    def __init__(self, scope, user, action, subject=None):
        self.scope = scope
        self.user = user
        if not action in self.ACTIONS:
            raise ValueError("Invalid action!")
        self.action = action
        if subject is None:
            subject = scope
        self._subject_entity = None
        self._tally = None
        self._stable = {}
        self._selection = None
        self.subject = subject

    @reconstructor
    def _reconstruct(self):
        self._subject_entity = None
        self._tally = None
        self._stable = {}
        self._selection = None

    def _get_subject(self):
        import refs
        if self._subject_entity is None:
            self._subject_entity = refs.to_entity(self._subject)
        return self._subject_entity

    def _set_subject(self, subject):
        import refs
        self._subject_entity = subject
        self._subject = refs.to_ref(subject)
        if self._subject is None:
            self._subject = subject

    subject = property(_get_subject, _set_subject)

    @property
    def selection(self):
        if self._selection is None:
            from selection import Selection
            self._selection = Selection.by_key(self._subject,
                                               instance_filter=False)
        return self._selection

    @property
    def variant(self):
        if self.selection is None:
            return None
        for (variant, poll) in self.selection.variant_polls:
            if poll == self:
                return variant

    @property
    def tally(self):
        if self._tally is None:
            if len(self.tallies):
                self._tally = self.tallies[0]
            else:
                from tally import Tally
                self._tally = Tally.create_from_poll(self)
        return self._tally

    def can_end(self):
        if self.has_ended():
            return False
        if self.action == self.RATE:
            return False
        if self.tally.has_majority() and self.tally.has_participation():
            return False
        return True

    def end(self, end_time=None):
        if end_time is None:
            end_time = datetime.utcnow()
        if not self.has_ended(at_time=end_time):
            self.end_time = end_time

    def has_ended(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.end_time is not None) \
            and self.end_time <= at_time

    def delete(self, delete_time=None):
        return self.end(end_time=delete_time)

    def is_deleted(self, at_time=None):
        return self.has_ended(at_time=at_time)

    def check_stable(self, at_time):
        from tally import Tally
        end = datetime.utcnow() if at_time is None else at_time
        start = end - self.scope.instance.activation_timedelta
        tallies = Tally.all_samples(self, start, end)
        if not len(tallies):
            return False
        if tallies[0].create_time > start:
            return False
        for tally in tallies:
            if not (tally.has_participation() and
                    tally.has_majority()):
                return False
        return True

    def is_stable(self, at_time=None):
        if not at_time in self._stable:
            self._stable[at_time] = self.check_stable(at_time)
        return self._stable[at_time]

    @classmethod
    def create(cls, scope, user, action, subject=None, with_vote=False):
        from tally import Tally
        from vote import Vote
        from adhocracy.lib.democracy import Decision
        poll = Poll(scope, user, action, subject=subject)
        meta.Session.add(poll)
        meta.Session.flush()
        if with_vote:
            decision = Decision(user, poll)
            decision.make(Vote.YES)
        Tally.create_from_poll(poll)
        meta.Session.flush()
        return poll

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=True):
        from delegateable import Delegateable
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.id == int(id))
            if not include_deleted:
                q = q.filter(or_(Poll.end_time == None,
                                 Poll.end_time > datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.join(Delegateable)
                q = q.filter(Delegateable.instance == ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def by_subjects(cls, subjects, include_deleted=True):
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.subject.in_(subjects))
            q = q.options(eagerload(Poll.tallies))
            if not include_deleted:
                q = q.filter(or_(Poll.end_time == None,
                                 Poll.end_time > datetime.utcnow()))
            return q.all()
        except Exception, e:
            log.exception("by_subjects(%s): %s" % (subjects, e), e)
            return []

    @classmethod
    def within_scope(cls, scope):
        def _crawl(scope):
            l = [scope]
            [l.extend(_crawl(c)) for c in scope.children]
            return l
        scope_ids = [s.id for s in _crawl(scope)]
        q = meta.Session.query(Poll)
        q = q.filter(Poll.scope_id.in_(scope_ids))
        q = q.filter(or_(Poll.end_time == None,
                         Poll.end_time > datetime.utcnow()))
        return q.all()

    def to_dict(self):
        from adhocracy.lib import helpers as h
        return dict(id=self.id,
                    user=self.user.user_name,
                    action=self.action,
                    begin_time=self.begin_time,
                    end_time=self.end_time,
                    tally=self.tally,
                    url=h.entity_url(self),
                    scope=self.scope,
                    subject=self.subject)

    def __repr__(self):
        return u"<Poll(%s,%s,%s,%s)>" % (self.id,
                                         self.scope_id,
                                         self.begin_time,
                                         self.end_time)
