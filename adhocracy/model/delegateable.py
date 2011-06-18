"""sqlalchemy model and table shared by all modes for which a user should
be able to delegate the voting to another user (
:py:class:`adhocracy.model.comment.Comment`,
:py:class:`adhocracy.model.proposal.Proposal` and
:py:class:`adhocracy.model.page.Page`).

SQLAlchemy's `joint table inheritance` is used.
"""

from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, String, Unicode

import meta
import instance_filter as ifilter

log = logging.getLogger(__name__)


# REFACT: this should not be used anymore - remove?
category_graph = Table('category_graph', meta.data,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )


delegateable_table = Table('delegateable', meta.data,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('milestone_id', Integer, ForeignKey('milestone.id'), nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )


class Delegateable(meta.Indexable):

    def __init__(self):
        raise Exception("Make a category or a proposal instead!")

    def init_child(self, instance, label, creator):
        self.instance = instance
        self.label = label
        self.creator = creator

    def __repr__(self):
        return u"<Delegateable(%d,%s)>" % (self.id, self.instance.key)

    def is_super(self, delegateable):
        if delegateable in self.children:
            return True
        for child in self.children:
            r = child.is_super(delegateable)
            if r:
                return True
        return False

    def is_sub(self, delegateable):
        return delegateable.is_super(self)

    def is_mutable(self):
        return True

    def _get_tags(self):
        _tags = dict()
        for tagging in self.taggings:
            _tags[tagging.tag] = _tags.get(tagging.tag, 0) + 1
        return sorted(_tags.items(), key=lambda (k, v): (v, k), reverse=True)

    tags = property(_get_tags)

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Delegateable)
            q = q.filter(Delegateable.id == int(id))
            if not include_deleted:
                q = q.filter(or_(Delegateable.delete_time == None,
                                 Delegateable.delete_time > datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter((Delegateable.instance_id ==
                              ifilter.get_instance().id))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Delegateable)
        if not include_deleted:
            q = q.filter(or_(Delegateable.delete_time == None,
                             Delegateable.delete_time > datetime.utcnow()))
        if instance is not None:
            q = q.filter(Delegateable.instance == instance)
        return q.all()

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time
        for child in self.children:
            child.delete(delete_time=delete_time)
        for delegation in self.delegations:
            delegation.delete(delete_time=delete_time)
        for comment in self.comments:
            comment.delete(delete_time=delete_time)
        for poll in self.polls:
            poll.end()
        for tagging in self.taggings:
            tagging.delete()

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time <= at_time

    def find_latest_comment_time(self):
        from revision import Revision
        from comment import Comment
        query = meta.Session.query(Revision.create_time)
        query = query.join(Comment)
        query = query.filter(Comment.topic == self)
        query = query.order_by(Revision.create_time.desc())
        query = query.limit(1)
        latest = query.first()
        if latest is None:
            return self.create_time
        else:
            return latest[0]

    def comment_count(self):
        return len([c for c in self.comments if not c.is_deleted()])

    def current_delegations(self):
        return filter(lambda d: not d.is_revoked(), self.delegations)

    def user_position(self, user):
        return 0

    def _index_id(self):
        return self.id

    def to_dict(self):
        from adhocracy.lib import helpers as h
        return dict(id=self.id,
                    label=self.label,
                    tags=dict([(k.name, v) for k, v in self.tags]),
                    url=h.entity_url(self),
                    instance=self.instance.key,
                    #comment=self.comment.id,
                    creator=self.creator.user_name,
                    create_time=self.create_time)

    def to_index(self):
        index = super(Delegateable, self).to_index()
        index.update(dict(
            instance=self.instance.key,
            title=self.title,
            tag=[k.name for k, v in self.tags],
            user=self.creator.user_name
            ))
        return index
