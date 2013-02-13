import logging
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, Unicode
from sqlalchemy.orm import reconstructor

import meta
import refs

log = logging.getLogger(__name__)


watch_table = Table(
    'watch', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('entity_type', Unicode(255), nullable=False, index=True),
    Column('entity_ref', Unicode(255), nullable=False, index=True)
)


class Watch(object):

    def __init__(self, user, entity):
        self.user = user
        self._entity = None
        self.entity = entity

    @reconstructor
    def _reconstruct(self):
        self._entity = None

    def _get_entity(self):
        if self._entity is None:
            self._entity = refs.to_entity(self.entity_ref)
        return self._entity

    def _set_entity(self, entity):
        self._entity = entity
        self.entity_ref = refs.to_ref(entity)
        self.entity_type = refs.entity_type(entity)

    entity = property(_get_entity, _set_entity)

    @classmethod
    def by_id(cls, id, include_deleted=False):
        try:
            q = meta.Session.query(Watch)
            q = q.filter(Watch.id == id)
            if not include_deleted:
                q = q.filter(or_(Watch.delete_time == None,
                                 Watch.delete_time > datetime.utcnow()))
            return q.limit(1).first()
        except:
            return None

    @classmethod
    def find_by_entity(cls, user, entity, include_deleted=False):
        return Watch.find(user, refs.to_ref(entity),
                          include_deleted=include_deleted)

    @classmethod
    def find(cls, user, ref, include_deleted=False):
        try:
            q = meta.Session.query(Watch)
            q = q.filter(Watch.user == user)
            q = q.filter(Watch.entity_ref == ref)
            if not include_deleted:
                q = q.filter(or_(Watch.delete_time == None,
                                 Watch.delete_time > datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s:%s): %s" % (user, ref, e))

    @classmethod
    def all_by_entity(self, entity):
        q = meta.Session.query(Watch)
        q = q.filter(Watch.entity_ref == refs.to_ref(entity))
        q = q.filter(or_(Watch.delete_time == None,
                         Watch.delete_time > datetime.utcnow()))
        return q.all()

    @classmethod
    def all_by_user(self, user):
        q = meta.Session.query(Watch)
        q = q.filter(Watch.user == user)
        q = q.filter(or_(Watch.delete_time == None,
                         Watch.delete_time > datetime.utcnow()))
        return q.all()

    @classmethod
    def all(cls, include_deleted=False):
        q = meta.Session.query(Watch)
        if not include_deleted:
            q = q.filter(or_(Watch.delete_time == None,
                             Watch.delete_time > datetime.utcnow()))
        return q.all()

    @classmethod
    def create(cls, user, entity):
        watch = Watch(user, entity)
        meta.Session.add(watch)
        meta.Session.flush()
        return watch

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if not self.is_deleted(delete_time):
            self.delete_time = delete_time

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return ((self.delete_time is not None) and
                self.delete_time <= at_time)

    def __repr__(self):
        return "<Watch(%s,%s,%s)>" % (self.id, self.user.user_name,
                                      self.entity_ref)
