from datetime import datetime, date, timedelta
import hashlib, logging

import simplejson

from pylons.i18n import _ 

from lucene import Document, Field, BooleanQuery, TermQuery, Term, Hit, BooleanClause

import adhocracy.model as model
from ..search import index 
from ..search import entityrefs
import util, types, formatting

log = logging.getLogger(__name__)

class Event(object):
        
    def __init__(self, event, data, agent, time=None, scopes=[], topics=[]):
        self.doc = Document()
        self.add_field("type", "event") 
        if not time:
            time = datetime.now()
        self.time = time  
        if not agent: 
            raise EventException("No agent for event %s" % event)      
        self.event = event
        if not agent: 
            raise EventException("No agent for event %s" % event)
        self.agent = agent
        self.scopes = scopes
        self.topics = topics
        self.data = data
        
    def add_field(self, name, value, store=True, tokenize=False):
        store = store and Field.Store.YES or Field.Store.NO
        tokenize = tokenize and Field.Index.TOKENIZED or Field.Index.UN_TOKENIZED
        self.doc.add(Field(name, unicode(value), store, tokenize))
    
    def _set_data(self, data):
        """
        For some known formatting elements, replace them with an ID 
        key-value pair that can later be used to reproduce the entity
        for formatting.
        """
        self._data = dict([(k, entityrefs.to_ref(v)) for k, v in data.items()])
        
    def _get_data(self):
        return self._data
    
    data = property(_get_data, _set_data)

    def format(self, decoder):
        """
        Given a dict of formatting options, load the appropriate 
        entities from the database and format them with the given 
        decoder.
        """
        def decode_kv(kv):
            if not isinstance(kv, basestring):
                return kv
            entity = entityrefs.to_entity(kv)
            if not entity:
                return _("(Undefined)")
            for cls in formatting.FORMATTERS.keys():
                if isinstance(entity, cls):
                    return decoder(formatting.FORMATTERS[cls], entity)
            return kv
        args = dict([(k, decode_kv(v)) for k, v in self.data.items()])
        return types.messages.get(self.event)() % args
    
    def html(self):
        return self.format(lambda formatter, value: formatter.html(value))
    
    def __unicode__(self):
        return self.format(lambda formatter, value: formatter.unicode(value))
                    
    def persist(self):
        """
        Persist the event to the lucene index. 
        """
        if self.exists():
            self.delete()
        self.add_field("time", self._str_time)
        self.add_field("event", self.event)
        self.add_field("_event_hash", str(hash(self)))
        self.add_field("agent", util.objtoken(self.agent))
        self.add_field("agent_id", self.agent.user_name)
        self.add_field("data", simplejson.dumps(self.data), 
                       store=True, tokenize=False)
        if not self.agent in self.topics:
            self.add_field("topic", util.objtoken(self.agent))
        [self.add_field("scope", util.objtoken(s)) for s in self.scopes]
        [self.add_field("topic", util.objtoken(t)) for t in self.topics]
        index.write_document(self.doc)
    
    @classmethod
    def restore(cls, doc):
        """
        Given a document from the lucene index, restore the Event to its 
        original state as far as possible. 
        """
        try:     
            agent_id = doc.getField("agent_id").stringValue()
            agent = model.User.find(agent_id, instance_filter=False)
            if not agent:
                raise util.EventException("Can't restore motion with non-existing agent: %s" % agent_id)
            data_json = doc.getField("data").stringValue()
            data = simplejson.loads(data_json)
            time_flat = doc.getField("time").stringValue()
            time = datetime.strptime(time_flat, formatting.DT_FORMAT)
            event = doc.getField("event").stringValue()
            return Event(event, data, agent, time)
        except ValueError, ve:
            raise EventException(ve)
        except AttributeError, ae:
            raise EventException(ae)
    
    @classmethod
    def by_hash(cls, hash):
        """
        Return a given event by its identifying hash value. If there is an error 
        during restoration, this may raise an EventException.
        """
        hquery = TermQuery(util.hash_term(hash))
        hits = index.query(hquery)
        if len(hits) > 1:
            raise util.EventException("Multiple events exist with hash %s" % hash)
        for hit in hits:
            hit = Hit.cast_(hit)
            doc = hit.getDocument()
            return cls.restore(doc)
        
    def exists(self):
        """
        Check if the event is already saved to the lucene index.
        """
        return not self.by_hash(hash(self)) == None
    
    def delete(self):
        """
        Delete the event from the lucene index if it exists. If it is not 
        stored yet, nothing will happen. 
        """
        index.delete_document(util.hash_term(hash(self)))
    
    def _get_time(self):
        return self._time
    
    def _set_time(self, time):
        self._str_time = time.strftime(formatting.DT_FORMAT)
        self._time = time
        
    time = property(_get_time, _set_time)
    create_time = property(_get_time, _set_time) # allow default sorters
    
    def __repr__(self):
        return "Event<%s: %s, %s>" % (repr(self.agent), self.event, self.data)
    
    def __hash__(self):
        hash = hashlib.sha1(str(self.time))
        hash.update(self.event)
        hash.update(self.agent.user_name) 
        return int(hash.hexdigest(), 16)
    
    def __eq__(self, other):
        return hash(self) == hash(other)
