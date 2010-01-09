from datetime import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, func, Boolean, Unicode, UnicodeText
from sqlalchemy.orm import synonym, reconstructor
from sqlalchemy.orm import relation, backref

import simplejson as json

import filter as ifilter
from meta import Base
import meta
import user
import refs

event_topic = Table('event_topic', Base.metadata,
    Column('event_id', Integer, ForeignKey('event.id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('topic_id', Integer, ForeignKey('delegateable.id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

class Event(Base):
    __tablename__ = 'event'
    
    id = Column(Integer, primary_key=True)
    _event = Column('event', Unicode(255), nullable=False)
    time = Column(DateTime, default=datetime.utcnow)
    _data = Column('data', UnicodeText(), nullable=False)
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relation(user.User, lazy=False, primaryjoin="Event.user_id==User.id")
    
    instance_id = Column(Integer, ForeignKey('instance.id'), nullable=True)
    instance = relation('Instance', lazy=True, primaryjoin="Event.instance_id==Instance.id")
    
    topics = relation('Delegateable', secondary=event_topic, lazy=True)
    
    def __init__(self, event_type, user, data, instance=None):
        self._event = unicode(event_type)
        self.user = user
        self.instance = instance
        self.data = data
    
    @reconstructor
    def _reconstruct(self):
        self._ref_data = json.loads(self._data)
        self._deref_data = {}
    
    def __repr__(self):
        return "<Event(%d,%s,%s,%s)>" % (self.id, self.event, self.time, 
                                         self.user.user_name)
    
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
    
    data = synonym('_data', descriptor=property(_get_data,
                                                _set_data))
    
    def _get_event(self):
        try:
            import adhocracy.lib.event.types as types
            for etype in types.TYPES:
                if str(etype) == self._event:
                    return etype
            return self._event
        except ImportError:
            return self._event
    
    event = synonym('_event', descriptor=property(_get_event))
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Event)
            q = q.filter(Event.id==id)
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Event.instance_id==ifilter.get_instance().id)
            return q.one()
        except:
            return None