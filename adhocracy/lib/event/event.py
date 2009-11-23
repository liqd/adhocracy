from datetime import datetime
import hashlib, logging

import simplejson as json

from pylons.i18n import _ 

from ..search import entityrefs
import types, formatting

log = logging.getLogger(__name__)

class EventException(Exception):
    pass

class EventFormattingException(EventException):
    pass

class Event(object):
    
    def __init__(self, event, agent, time=None, 
                 scopes=[], topics=[], **data):
        if not time:
            time = datetime.now()
        if not agent: 
            raise EventException("No agent for event %s" % event)
        data['event'] = event
        data['agent'] = agent
        data['time'] = int(time.strftime('%s'))
        data['scopes'] = scopes
        data['topics'] = topics
        self._data = data
        
    def _get_time(self):
        return datetime.fromtimestamp(self._data['time'])
    
    time = property(_get_time)
    create_time = property(_get_time) # allow default sorters
        
    def __getattr__(self, attr):
        return self._data.get(attr)
    
    def __hash__(self):
        hash = hashlib.sha1(str(self._data['time']))
        hash.update(self.event)
        hash.update(self.agent.user_name) 
        return int(hash.hexdigest(), 16)
    
    id = property(lambda self: hash(self))
    
    def to_json(self):
        ref_data = entityrefs.refify(self._data) 
        return json.dumps(ref_data)
    
    @classmethod
    def from_json(cls, data):
        deref_data = entityrefs.derefify(json.loads(data))
        for key in ['event', 'agent', 'time', 'scopes', 'topics']:
            if not key in deref_data.keys():
                raise EventException("Incomplete JSON Event: %s missing" % key)
        time = datetime.fromtimestamp(deref_data['time'])
        kwargs = dict([(str(k), v) for k, v in deref_data.items() \
                      if not k in [u"time", u"event", u"agent"]])
        return cls(deref_data['event'], deref_data['agent'], time=time, **kwargs)
    
    def format(self, decoder):
        """
        Given a dict of formatting options, load the appropriate 
        entities from the database and format them with the given 
        decoder.
        """
        def format_value(value):
            for cls in formatting.FORMATTERS.keys():
                if isinstance(value, cls):
                    return decoder(formatting.FORMATTERS[cls], value)
            return value
        args = dict([(k, format_value(v)) for k, v in self._data.items() \
                     if k not in ['agent', 'topics', 'scopes']])
        return types.messages.get(self.event)() % args
    
    def html(self):
        return self.format(lambda formatter, value: formatter.html(value))
    
    def __unicode__(self):
        return self.format(lambda formatter, value: formatter.unicode(value))
    
    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def __repr__(self):
        return "Event<%s:%s,%s>" % (self.agent.user_name, self.event, self.time)
    
    
    



















class OldEvent(object):
        
    def __init__(self, event, data, agent, time=None, scopes=[], topics=[]):
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
                    
    
        
    
    def _get_time(self):
        return self._time
    
    def _set_time(self, time):
        self._str_time = time.strftime(formatting.DT_FORMAT)
        self._time = time
        
    time = property(_get_time, _set_time)
    create_time = property(_get_time, _set_time) # allow default sorters
    
    
    def __hash__(self):
        hash = hashlib.sha1(str(self.time))
        hash.update(self.event)
        hash.update(self.agent.user_name) 
        return int(hash.hexdigest(), 16)
    
    def __eq__(self, other):
        return hash(self) == hash(other)
