from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, PickleType
from sqlalchemy import Integer, DateTime, or_
from sqlalchemy.orm import reconstructor

import meta
import instance_filter as ifilter

log = logging.getLogger(__name__)


def are_elements_equal(x, y):
    return x == y

selection_table = Table(
    'selection', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('page_id', Integer, ForeignKey('page.id',
           name='selection_page', use_alter=True), nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id',
           name='selection_proposal', use_alter=True), nullable=True),
    Column('variants', PickleType(comparator=are_elements_equal),
           nullable=True)
)


class Selection(object):

    def __init__(self, page, proposal, variant=None):
        '''
        Create a new Selection.

        page (:class:`adhocracy.model.page.Page`)
            The selected page
        proposal (:class:`adhocracy.mode.page.Page`)
            The proposal from which the page is selected
        variant `str`
            The variant for which the selection is valid
        '''
        from text import Text
        self.page = page
        self.proposal = proposal
        self._polls = None
        self.variants = [Text.HEAD]
        if variant is not None:
            self.variants.append(variant)

    @reconstructor
    def _reconstruct(self):
        self._polls = None

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        from proposal import Proposal
        try:
            q = meta.Session.query(Selection)
            q = q.filter(Selection.id == id)
            if not include_deleted:
                q = q.filter(or_(Selection.delete_time == None,
                                 Selection.delete_time > datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.join(Proposal)
                q = q.filter(Proposal.instance == ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def by_page(cls, page):
        return cls.by_page_and_proposal(page, None)

    @classmethod
    def by_variant(cls, page, variant, proposal=None):
        '''
        Return a list of selections for a *variant*. If a *proposal* is
        given, only the selections for related to the *proposal* are
        returned.

        page:
            A :class:`adhocracy.model.page.Page` object
        variant (str):
            The variant name.
        proposal:
            A :class:`adhocracy.model.proposal.Proposal` object

        Returns: A `list` of :class:`adhocracy.model.selection.Selection`
        objects.
        '''
        selections = cls.by_page_and_proposal(page, proposal)
        return [selection for selection in selections if variant in
                selection.variants]

    @classmethod
    def by_page_and_proposal(cls, page, proposal):
        try:
            q = meta.Session.query(Selection)
            q = q.filter(Selection.page == page)
            if proposal is not None:
                q = q.filter(Selection.proposal == proposal)
            q = q.filter(or_(Selection.delete_time == None,
                             Selection.delete_time > datetime.utcnow()))
            return q.all()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def by_key(cls, key, **kwargs):
        id = int(key.split(':', 1)[1].split(']', 1)[0])
        return cls.find(id, **kwargs)

    @classmethod
    def create(cls, proposal, page, user, variant=None):
        selections = cls.by_page_and_proposal(page, proposal)
        if len(selections):
            selection = selections[0]
            if variant is not None and variant not in selection.variants:
                selection.add_variant(variant)
                selection.make_variant_poll(variant, user)
            return selection
        selection = Selection(page, proposal, variant=variant)
        meta.Session.add(selection)
        page.parents.append(proposal)
        meta.Session.flush()
        for variant in page.variants:
            selection.make_variant_poll(variant, user)
        return selection

    def make_variant_poll(self, variant, user):
        from poll import Poll
        if variant not in self.variants:
            return None
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

    def add_variant(self, variant):
        assert variant in self.page.variants
        assert not self.by_variant(self.page, variant)
        if variant is None:
            return
        if variant in self.variants:
            return
        self.variants.append(variant)

    @property
    def subjects(self):
        variants = self.variants or []
        return [self.variant_key(v) for v in self.page.variants
                if v in variants]

    @property
    def polls(self):
        from poll import Poll
        if self._polls is None:
            self._polls = Poll.by_subjects(self.subjects)
        return self._polls

    @property
    def variant_polls(self):
        pairs = []
        for poll in self.polls:
            for variant in self.page.variants:
                if self.variant_key(variant) == poll.subject:
                    pairs.append((variant, poll))
        return sorted(pairs, key=lambda (k, v): v.tally.score, reverse=True)

    def variant_poll(self, variant):
        for (_variant, poll) in self.variant_polls:
            if variant == _variant:
                return poll
        return None

    @property
    def selected(self):
        from text import Text
        variant_polls = self.variant_polls
        if not len(variant_polls):
            return Text.HEAD
        sel_var, sel_poll = variant_polls[0]
        if len(variant_polls) > 1:
            next_var, next_poll = variant_polls[1]
            if sel_poll.tally.score == next_poll.tally.score:
                return None
        return sel_var

    @property
    def changes_text(self):
        from text import Text
        selected = self.selected
        if selected is None:
            return False
        if selected == Text.HEAD:
            return False
        return True

    def to_dict(self):
        d = dict(id=self.id,
                 create_time=self.create_time,
                 page=self.page.id,
                 proposal=self.proposal.id)
        return d

    def __repr__(self):
        id_ = self.proposal.id if self.proposal else "-"
        return u"<Selection(%d,%s,%s)>" % (self.id, self.page.id, id_)

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time
        for poll in self.polls:
            poll.end(delete_time)

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return ((self.delete_time is not None) and
                self.delete_time <= at_time)
