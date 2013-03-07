from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import DateTime, Integer, Unicode, UnicodeText
from sqlalchemy.orm import reconstructor

import json

import instance_filter as ifilter
import meta
import refs


log = logging.getLogger(__name__)


event_topic_table = Table(
    'event_topic', meta.data,
    Column('event_id', Integer, ForeignKey('event.id',
           onupdate="CASCADE", ondelete="CASCADE")),
    Column('topic_id', Integer, ForeignKey('delegateable.id',
           onupdate="CASCADE", ondelete="CASCADE"))
)


event_table = Table(
    'event', meta.data,
    Column('id', Integer, primary_key=True),
    Column('event', Unicode(255), nullable=False),
    Column('time', DateTime, default=datetime.utcnow),
    Column('data', UnicodeText(), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True)
)


class Event(object):

    def __init__(self, event_type, user, data, instance=None):
        self._event = unicode(event_type)
        self.user = user
        self.instance = instance
        self.data = data

    @reconstructor
    def _reconstruct(self):
        self._ref_data = json.loads(self._data)
        self._deref_data = {}

    def __getattr__(self, attr):
        if attr in ['_ref_data', '_deref_data']:
            raise AttributeError()
        if not attr in self._deref_data:
            if not attr in self._ref_data:
                raise AttributeError()
            val = self._ref_data.get(attr)
            self._deref_data[attr] = refs.complex_to_entities(val)
        return self._deref_data.get(attr)

    def __getitem__(self, item):
        # for string formatting
        return getattr(self, item)

    def _get_data(self):
        return refs.complex_to_entities(self._ref_data)

    def _set_data(self, data):
        self._deref_data = data
        self._ref_data = refs.complex_to_refs(data)
        self._data = unicode(json.dumps(self._ref_data))

    data = property(_get_data, _set_data)

    def _get_event(self):
        try:
            import adhocracy.lib.event.types as types
            for etype in types.TYPES:
                if str(etype) == self._event:
                    return etype
            return None
        except ImportError:
            return None

    event = property(_get_event)

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Event)
            q = q.filter(Event.id == id)
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Event.instance_id == ifilter.get_instance().id)
            return q.one()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def find_by_topics(cls, topics, limit=None):
        from delegateable import Delegateable
        topics = map(lambda d: d.id, topics)
        q = meta.Session.query(Event)
        q = q.join(Event.topics)
        q = q.filter(Delegateable.id.in_(topics))
        q = q.order_by(Event.time.desc())
        if ifilter.has_instance():
            q = q.filter(Event.instance_id == ifilter.get_instance().id)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    @classmethod
    def find_by_topic(cls, topic, limit=None):
        return Event.find_by_topics([topic], limit=limit)

    @classmethod
    def find_by_instance(cls, instance, limit=50):
        q = meta.Session.query(Event)
        q = q.filter(Event.instance == instance)
        q = q.order_by(Event.time.desc())
        q = q.limit(limit)
        return q.all()

    def text(self):
        text = None
        try:
            if self.event:
                from adhocracy.lib.text import render
                text = self.event.text(self)
                text = render(text)
        except AttributeError, ae:
            log.exception("Creating event text", ae)
        if text is None or not len(text):
            text = ''
        return text

    def link(self):
        try:
            if not self.event:
                return None
            return self.event.link_path(self)
        except:
            from adhocracy.lib import helpers as h
            if self.instance:
                return h.entity_url(self.instance)
            return h.base_url(instance=None)

    def to_dict(self):
        d = dict(id=self.id,
                 time=self.time,
                 data=self.data,
                 url=self.link(),
                 user=self.user.user_name,
                 event=self._event,
                 instance=self.instance and self.instance.key or None)
        d['topics'] = map(lambda t: t.id, self.topics)
        return d

    def __repr__(self):
        return "<Event(%d,%s,%s,%s)>" % (self.id, self.event, self.time,
                                         self.user.user_name)
