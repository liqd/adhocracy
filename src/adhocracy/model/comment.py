from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Boolean, Integer, Unicode

import meta
import instance_filter as ifilter


log = logging.getLogger(__name__)


comment_table = Table(
    'comment', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=None, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('wiki', Boolean, default=False),
    Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('variant', Unicode(255), nullable=True)
)


class Comment(meta.Indexable):

    SENT_PRO = 1
    SENT_CON = -1

    def __init__(self, topic, creator, variant):
        self.topic = topic
        self.creator = creator
        self.variant = variant

    def _get_latest(self):
        return self.revisions[0] if len(self.revisions) else None

    def _set_latest(self, rev):
        return self.revisions.insert(0, rev)

    latest = property(_get_latest, _set_latest)

    def root(self):
        return self if self.reply is None else self.reply.root()

    @property
    def is_root(self):
        return self.reply is None

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Comment)
            q = q.filter(Comment.id == id)
            if not include_deleted:
                q = q.filter(or_(Comment.delete_time == None,
                                 Comment.delete_time > datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def all_q(cls, instance_filter=True, include_deleted=False):
        from delegateable import Delegateable
        q = meta.Session.query(Comment)
        q = q.join(Delegateable)
        if ifilter.has_instance() and instance_filter:
            q = q.filter(Delegateable.instance_id == ifilter.get_instance().id)
        if not include_deleted:
            q = q.filter(or_(Comment.delete_time == None,
                             Comment.delete_time > datetime.utcnow()))
        return q

    @classmethod
    def all(cls, instance_filter=True, include_deleted=False):
        return cls.all_q(instance_filter=instance_filter,
                         include_deleted=include_deleted).all()

    @classmethod
    def create(cls, text, user, topic, reply=None, wiki=True,
               variant=None,
               sentiment=0, with_vote=False):
        from poll import Poll
        from text import Text
        if variant is None:
            variant = Text.HEAD
        comment = Comment(topic, user, variant)
        comment.wiki = wiki
        comment.reply = reply
        meta.Session.add(comment)
        meta.Session.flush()
        poll = Poll.create(topic, user, Poll.RATE, comment,
                           with_vote=with_vote)
        comment.poll = poll
        comment.latest = comment.create_revision(
            text, user, sentiment=sentiment,
            create_time=comment.create_time)
        return comment

    def create_revision(self, text, user, sentiment=0,
                        create_time=None):
        from revision import Revision
        rev = Revision(self, user, text)
        rev.sentiment = sentiment
        if create_time is not None:
            rev.create_time = create_time
        meta.Session.add(rev)
        self.revisions.append(rev)
        meta.Session.flush()
        return rev

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time
            if self.poll is not None:
                self.poll.end()

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
            self.delete_time <= at_time

    def is_edited(self):
        if self.is_deleted():
            return False
        return self.latest.create_time != self.create_time

    def is_mutable(self):
        return True  # self.topic.is_mutable()

    def _index_id(self):
        return self.id

    def to_dict(self):
        from adhocracy.lib import helpers as h
        d = dict(id=self.id,
                 create_time=self.create_time,
                 topic=self.topic_id,
                 url=h.entity_url(self, comment_page=True),
                 creator=self.creator.user_name)
        d['reply'] = self.reply_id
        d['wiki'] = self.wiki
        d['latest'] = self.latest.to_dict()
        d['revisions'] = map(lambda r: r.id, self.revisions)
        return d

    def to_index(self):
        index = super(Comment, self).to_index()
        if self.latest is not None:
            index.update(dict(
                tag=[],
                body=self.latest.text,
                user=self.creator.user_name
            ))
        if self.topic and self.topic.instance:
            index['instance'] = self.topic.instance.key
        return index

    def __repr__(self):
        return "<Comment(%d,%s,%d,%s)>" % (self.id, self.creator.user_name,
                                           self.topic_id, self.create_time)
