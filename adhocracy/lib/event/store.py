from datetime import datetime, date, timedelta
import hashlib, logging

import simplejson

from pylons.i18n import _ 

from lucene import Document, Field, BooleanQuery, TermQuery, Term, BooleanClause

import adhocracy.model as model
from ..search import index 
from ..search import entityrefs
import types, formatting
from event import Event, EventException

log = logging.getLogger(__name__)

class EventStore(object):
    
    def __init__(self, event):
        self.event = event    
        self.doc = Document()
        self.add_field("type", "event") 
        
    def add_field(self, name, value, store=True, tokenize=False):
        store = store and Field.Store.YES or Field.Store.NO
        tokenize = tokenize and Field.Index.TOKENIZED or Field.Index.UN_TOKENIZED
        self.doc.add(Field(name, unicode(value), store, tokenize))
        
    def get_time(self):
        return self.event.time.strftime(formatting.DT_FORMAT)
        
    def persist(self):
        """
        Persist the event to the lucene index. 
        """
        if self.exists():
            self.delete()
        self.add_field("time", self.get_time())
        self.add_field("event", self.event.event)
        self.add_field("_event_id", self.event.id)
        self.add_field("agent", self.objtoken(self.event.agent))
        self.add_field("data", self.event.to_json(), 
                       store=True, tokenize=False)
        if not self.event.agent in self.event.topics:
            self.add_field("topic", self.objtoken(self.event.agent))
        [self.add_field("scope", self.objtoken(s)) for s in self.event.scopes]
        [self.add_field("topic", self.objtoken(t)) for t in self.event.topics]
        index.write_document(self.doc)
    
    def exists(self):
        """
        Check if the event is already saved to the lucene index.
        """
        return not self.by_id(self.event.id) == None
    
    @classmethod
    def _id_term(cls, hash):
        """
        Creates a lucene query term that uniquely searches for this item.
        """
        return Term("_event_id", str(hash))
    
    def delete(self):
        """
        Delete the event from the lucene index if it exists. If it is not 
        stored yet, nothing will happen. 
        """
        index.delete_document(self._id_term(self.event.id))
    
    @classmethod
    def by_id(cls, id):
        """
        Return a given event by its identifying hash value. If there is an error 
        during restoration, this may raise an EventException.
        """
        hquery = TermQuery(cls._id_term(id))
        hits = index.query(hquery)
        if len(hits) > 1:
            raise util.EventException("Multiple events exist with hash %s" % hash)
        for hit in hits:
            hit = Hit.cast_(hit)
            doc = hit.getDocument()
            return cls._restore(doc)
    
    @classmethod
    def _restore(cls, doc):
        """
        Given a document from the lucene index, restore the Event to its 
        original state as far as possible. 
        """
        data_json = doc.getField("data").stringValue()
        return Event.from_json(data_json)
        
    @classmethod
    def objtoken(cls, obj):
        """
        Encode some known object types for use in event topic, scope, etc.
        Maybe this could be replaced by generic hashing? The current method 
        has the advantage of allowing admins to hand-write queries at some 
        point. 
        """
        if isinstance(obj, model.User):
            return "user.%s" % obj.user_name.lower()
        elif isinstance(obj, model.Category):
            return "category.%s" % obj.id.lower()
        elif isinstance(obj, model.Motion):
            return "motion.%s" % obj.id.lower()
        elif isinstance(obj, model.Issue):
            return "issue.%s" % obj.id.lower()
        elif isinstance(obj, model.Delegation):
            return "delegation.%s" % obj.id
        elif isinstance(obj, model.Instance):
            return "instance.%s" % obj.key.lower()
        return "str." + str(obj)

