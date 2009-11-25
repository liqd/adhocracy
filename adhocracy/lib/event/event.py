from datetime import datetime
import hashlib, logging

import simplejson as json

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
        if not self._data.get('id'):
            hash = hashlib.sha1(str(self._data['time']))
            hash.update(str(self.event))
            hash.update(self.agent.user_name) 
            self._data['id'] = abs(int(hash.hexdigest(), 16))
        return self._data['id']
    
    id = property(lambda self: hash(self))
    
    def to_json(self):
        ref_data = entityrefs.refify(self._data) 
        ref_data['event'] = str(ref_data.get('event'))
        return json.dumps(ref_data)
    
    @classmethod
    def from_json(cls, data):
        deref_data = entityrefs.derefify(json.loads(data))
        
        for key in ['event', 'agent', 'time', 'scopes', 'topics']:
            if not key in deref_data.keys():
                raise EventException("Incomplete JSON Event: %s missing" % key)

        for event in types.TYPES:
            if str(event) == deref_data['event']:
                deref_data['event'] = event
                
        time = datetime.fromtimestamp(deref_data['time'])
        kwargs = dict([(str(k), v) for k, v in deref_data.items() \
                      if not k in [u"time", u"event", u"agent"]])
        
        return cls(deref_data['event'], deref_data['agent'], time=time, **kwargs)
    
    def formatted_data(self, decoder):
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
        return dict([(k, format_value(v)) for k, v in self._data.items() \
                     if k not in ['topics', 'scopes']])
    
    def html(self):
        data = self.formatted_data(lambda formatter, value: formatter.html(value))
        return self.event.event_msg() % data
    
    def plain(self):
        data = self.formatted_data(lambda formatter, value: formatter.unicode(value))
        return self.event.event_msg() % data
    
    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def __repr__(self):
        return "Event<%s:%s,%s>" % (self.agent.user_name, self.event, self.time)
    
    def __str__(self):
        return repr(self)
    
