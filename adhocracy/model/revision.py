from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Unicode, UnicodeText, DateTime

import meta

log = logging.getLogger(__name__)

revision_table = Table('revision', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('text', UnicodeText(), nullable=False),
    Column('sentiment', Integer, default=0),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False),
    Column('title', Unicode(255), nullable=True)
    )


class Revision(object):

    def __init__(self, comment, title, user, text):
        self.comment = comment
        self.title = title
        self.user = user
        self.text = text

    @property
    def has_title(self):
        return self._title is not None

    def _get_title(self):
        if self.has_title:
            return self._title
        from adhocracy.lib.helpers import propose_comment_title
        return propose_comment_title(parent=self.comment.reply,
                                     topic=self.comment.topic,
                                     variant=self.comment.variant)

    def _set_title(self, title):
        self._title = title

    title = property(_get_title, _set_title)

    @property
    def is_earliest(self):
        return self == min(self.comment.revisions, key=lambda r: r.create_time)

    @property
    def is_latest(self):
        return self.comment.latest.id == self.id

    @property
    def previous(self):
        if not self.is_earliest:
            smaller = filter(lambda r: r.create_time < self.create_time,
                             self.comment.revisions)
            return max(smaller, key=lambda r: r.create_time)

    @property
    def index(self):
        return len(self.comment.revisions) - self.comment.revisions.index(self)

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Revision)
            q = q.filter(Revision.id == id)
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    def to_dict(self):
        d = dict(id=self.id,
                 title=self.title,
                 comment=self.comment_id,
                 create_time=self.create_time,
                 user=self.user.user_name,
                 text=self.text)
        return d

    def _index_id(self):
        return self.id

    def __repr__(self):
        return u"<Revision(%d,%s,%s)>" % (self.id,
                                          self.user.user_name,
                                          self.comment_id)
