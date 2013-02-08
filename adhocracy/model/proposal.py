import logging
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, Integer, Boolean, or_
from sqlalchemy.orm import reconstructor, eagerload

import meta
import instance_filter as ifilter

from delegateable import Delegateable

log = logging.getLogger(__name__)


proposal_table = Table(
    'proposal', meta.data,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('description_id', Integer, ForeignKey('page.id'), nullable=True),
    Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('adopted', Boolean, default=False)
)


class Proposal(Delegateable):

    def __init__(self, instance, label, creator):
        self.init_child(instance, label, creator)
        self._current_alternatives = None

    @reconstructor
    def _reconstruct(self):
        self._current_alternatives = None

    @property
    def selections(self):
        return [s for s in self._selections if not s.is_deleted()]

    @property
    def title(self):
        if self.description is None or self.description.head is None:
            return self.label
        return self.description.title

    @property
    def full_title(self):
        return self.title

    def is_adopt_polling(self):
        return (self.adopt_poll is not None) and \
            (not self.adopt_poll.has_ended())

    def is_mutable(self):
        return (not self.is_adopt_polling()) and (not self.adopted) and \
            (not self.instance.frozen)

    def has_implementation(self):
        from text import Text
        for selection in self.selections:
            selected = selection.selected
            if selected is not None and selected != Text.HEAD:
                return True
        return False

    def can_adopt(self):
        return not self.is_adopt_polling() \
            and self.instance.allow_adopt \
            and (not self.instance.use_norms or self.has_implementation()) \
            and not self.adopted

    def adopt(self, at_time=None):
        from text import Text
        if at_time is None:
            at_time = datetime.utcnow()
        if not self.is_adopt_polling():
            return
        for selection in self.selections:
            selected = selection.selected
            if selected is None or selected == Text.HEAD:
                continue
            if not selected in selection.page.variants:
                continue
            source_text = selection.page.variant_at(selected,
                                                    self.adopt_poll.begin_time)
            dest_text = Text.create(selection.page,
                                    Text.HEAD,
                                    source_text.user,
                                    selection.page.head.title,
                                    source_text.text,
                                    parent=source_text,
                                    wiki=source_text.wiki)
            dest_text.create_time = at_time
        self.adopted = True
        meta.Session.commit()
        self.adopt_poll.end(at_time)
        meta.Session.flush()

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False, full=False):
        try:
            q = meta.Session.query(Proposal)
            id = int(unicode(id).split('-', 1)[0])
            q = q.filter(Proposal.id == id)
            if full:
                q = q.options(eagerload(Proposal.comments))
                q = q.options(eagerload(Proposal.adopt_poll))
                q = q.options(eagerload(Proposal.rate_poll))
                q = q.options(eagerload(Proposal.taggings))
                q = q.options(eagerload(Proposal.parents))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Proposal.instance_id == ifilter.get_instance().id)
            if not include_deleted:
                q = q.filter(or_(Proposal.delete_time == None,
                                 Proposal.delete_time > datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def find_all(cls, ids, instance_filter=True, include_deleted=False):
        q = meta.Session.query(Proposal)
        q = q.filter(Proposal.id.in_(ids))
        if ifilter.has_instance() and instance_filter:
            q = q.filter(Proposal.instance_id == ifilter.get_instance().id)
        if not include_deleted:
            q = q.filter(or_(Proposal.delete_time == None,
                             Proposal.delete_time > datetime.utcnow()))
        return q.all()

    @classmethod
    def find_by_creator(cls, user, instance_filter=True):
        q = meta.Session.query(Proposal)
        q = q.filter(Proposal.creator == user)
        q = q.filter(or_(Proposal.delete_time == None,
                         Proposal.delete_time > datetime.utcnow()))
        if ifilter.has_instance() and instance_filter:
            q = q.filter(Proposal.instance_id == ifilter.get_instance().id)
        return q.all()

    @classmethod
    def all_q(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Proposal)
        if not include_deleted:
            q = q.filter(or_(Proposal.delete_time == None,
                             Proposal.delete_time > datetime.utcnow()))
        if instance is not None:
            q = q.filter(Proposal.instance == instance)
        return q

    @classmethod
    def all(cls, instance=None, include_deleted=False):
        return cls.all_q(instance=instance,
                         include_deleted=include_deleted).all()

    @classmethod
    def create(cls, instance, label, user, with_vote=False, tags=None):
        from poll import Poll
        from tagging import Tagging
        proposal = Proposal(instance, label, user)
        meta.Session.add(proposal)
        meta.Session.flush()
        poll = Poll.create(proposal, user, Poll.RATE,
                           with_vote=with_vote)
        proposal.rate_poll = poll
        if tags is not None:
            proposal.taggings = Tagging.create_all(proposal, tags, user)
        meta.Session.flush()
        return proposal

    @classmethod
    def filter_by_state(cls, state, proposals):
        if state:
            filtered = []
            for proposal in proposals:
                if state == u'draft' and not proposal.is_adopt_polling() \
                        and not proposal.adopted:
                    filtered.append(proposal)
                elif state == u'polling' and proposal.is_adopt_polling():
                    filtered.append(proposal)
                elif state == u'adopted' and proposal.adopted:
                    filtered.append(proposal)
            return filtered

    def delete(self, delete_time=None):
        '''
        Delete the proposal and all it's selections
        (proposal-norm(page)-relations), but not the norms.
        '''
        if delete_time is None:
            delete_time = datetime.utcnow()

        # We don't want to delete the children of this
        # Delegateable cause these are the related norms.
        Delegateable.delete(self, delete_time=delete_time,
                            delete_children=False)

        for selection in self.selections:
            selection.delete(delete_time=delete_time)

    def comment_count(self):
        if not self.description:
            return 0
        return self.description.comment_count()

    def find_latest_comment_time(self):
        if not self.description:
            return None
        return self.description.find_latest_comment_time()

    def user_position(self, user):
        from pylons import tmpl_context as c
        if not user:
            return 0
        if not c.proposal_pos:
            c.proposal_pos = {}
            if not self.id in c.proposal_pos:
                c.proposal_pos[self.id] = c.user.any_position_on_proposal(self)
            return c.proposal_pos[self.id]

    def to_index(self):
        index = super(Proposal, self).to_index()
        if self.description is not None and self.description.head is not None:
            index.update(dict(
                body=self.description.head.text,
            ))
        return index

    def __repr__(self):
        return u"<Proposal(%s)>" % self.id
