from datetime import datetime
import logging

from pylons.i18n import _
from sqlalchemy import Column, ForeignKey, Table, or_
from sqlalchemy import Boolean, Integer, Unicode, UnicodeText, DateTime

import meta

log = logging.getLogger(__name__)

milestone_table = Table('milestone', meta.data,
    Column('id', Integer, primary_key=True),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('title', Unicode(255), nullable=True),
    Column('text', UnicodeText(), nullable=True),
    Column('time', DateTime),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime)
    )


class Milestone(object):

    def __init__(self, instance, creator, title, text, time):
        self.instance = instance
        self.creator = creator
        self.title = title
        self.text = text
        self.time = time

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        q = meta.Session.query(Milestone)
        q = q.filter(Milestone.id == id)
        if not include_deleted:
            q = q.filter(or_(Milestone.delete_time == None,
                             Milestone.delete_time > datetime.utcnow()))
        return q.first()

    @classmethod
    def create(cls, instance, creator, title, text, time):
        milestone = Milestone(instance, creator, title, text, time)
        meta.Session.add(milestone)
        meta.Session.flush()
        return milestone

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return ((self.delete_time is not None) and
                self.delete_time <= at_time)

    def _index_id(self):
        return self.id

    def to_dict(self):
        from adhocracy.lib import helpers as h
        d = dict(id=self.id,
                 title=self.title,
                 url=h.entity_url(self),
                 create_time=self.create_time,
                 text=self.text,
                 creator=self.creator.user_name,
                 instance=self.instance.key)
        return d

    def to_index(self):
        index = super(Milestone, self).to_index()
        index.update(dict(
            instance=self.instance.key,
            title=self.title,
            tags=[],
            body=self.text,
            user=self.creator.user_name
            ))
        return index

    def __repr__(self):
        title = self.title.encode('ascii', 'replace')
        return u"<Milestone(%s, %s, %s)>" % (self.id, title, 
                self.time.isoformat())

