from adhocracy.tests import *
from adhocracy.tests.testtools import *
from datetime import datetime
import adhocracy.lib.event as e
import adhocracy.model as model

class TestEvent(TestController):
    
    def test_emit_creates_index_entry(self):
        admin = tt_get_admin()
        evt = e.emit(e.T_TEST, admin, test="test")
        es = e.EventStore(evt)
        assert es.exists()
        #evt.delete()
        
    def test_all_entity_persitence_and_restoration(self):
        topic = tt_make_str()
        admin = tt_get_admin()
        
        evt = e.Event(e.T_TEST, admin, topics=[topic], test="test")
        assert evt.agent != None
        assert evt.agent == admin
        assert evt.time != None
        assert evt.topics != None
        assert topic in evt.topics 
        assert evt.scopes != None
        assert not len(evt.scopes)
        #assert not evt.exists()
        es = e.EventStore(evt)
        
        es.persist()
        assert es.exists()
        
        p_evt = e.EventStore.by_id(evt.id)
        assert p_evt.agent != None
        assert p_evt.agent == admin
        assert p_evt.time != None
        assert p_evt.topics != None
        assert topic in p_evt.topics 
        assert p_evt.scopes != None
        assert not len(p_evt.scopes)
        
        es.delete()
        assert not es.exists()
    
    def test_hash_identical_for_event_with_equal_key_properties(self):
        admin = tt_get_admin()
        tm = datetime.now()
        
        evt1 = e.Event(e.T_TEST, admin, time=tm, test='test')
        evt2 = e.Event(e.T_TEST, admin, time=tm, test='test')
        assert evt1 == evt1
        assert evt1.time == evt2.time
        assert evt1 == evt2
        assert hash(evt1) == hash(evt2) 
    
    def test_query_by_topic_and_scope(self):
        topic1 = 'hello'
        topic2 = 'world'
        admin = tt_get_admin()
        
        print "E", e.emit(e.T_TEST, admin, topics=[topic1], scopes=[topic1], test='test')
        print "E", e.emit(e.T_TEST, admin, topics=[topic2], test='test')
        print "E", e.emit(e.T_TEST, admin, topics=[topic1, topic2], test='test')
        
        r = e.q.run(e.q.topic(topic1))
        assert len(r) == 2
        r = e.q.run(e.q.topic(topic2))
        assert len(r) == 2
        r = e.q.run(e.q._or(e.q.topic(topic1), e.q.topic(topic2)))
        assert len(r) == 3
        r = e.q.run(e.q._and(e.q.topic(topic1), e.q.topic(topic2)))
        assert len(r) == 1
        r = e.q.run(e.q._and(e.q.topic(topic1), e.q._not(e.q.topic(topic2))))
        assert len(r) == 1
        r = e.q.run(e.q.scope(topic1))
        assert len(r) == 1
        r = e.q.run(e.q._and(e.q.topic(topic1), e.q.agent(admin)))
        assert len(r) == 2

        