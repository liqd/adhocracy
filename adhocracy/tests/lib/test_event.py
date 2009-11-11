from adhocracy.tests import *
from adhocracy.tests.testtools import *
from datetime import datetime
import adhocracy.lib.event as e
import adhocracy.model as model

class TestEvent(TestController):
    
    def test_emit(self):
        admin = tt_get_admin()
        evt = e.emit(e.T_TEST, {'test': "test"}, admin)
        assert evt.exists()
        evt.delete()
        
    def test_all_persistence(self):
        topic = tt_make_str()
        admin = tt_get_admin()
        
        evt = e.Event(e.T_TEST, {'test': "test"}, admin)
        assert evt.agent != None
        assert evt.time != None
        assert evt.topics != None
        assert evt.scopes != None
        assert not evt.exists()
        
        evt.persist()
        assert evt.exists()
        
        evt.delete()
        assert not evt.exists()
    
    def test_hash(self):
        admin = tt_get_admin()
        tm = datetime.now()
        
        evt1 = e.Event(e.T_TEST, {'test': "test"}, admin, time=tm)
        evt2 = e.Event(e.T_TEST, {'test': "test"}, admin, time=tm)
        assert evt1 == evt1
        assert evt1.time == evt2.time
        assert evt1 == evt2
        assert hash(evt1) == hash(evt2) 
        evt1.persist()
        assert evt2.exists()
    
    def test_query(self):
        topic1 = tt_make_str()
        topic2 = tt_make_str()
        admin = tt_get_admin()
        #print "TOPIC ", topic
        e.emit(e.T_TEST, {'test': 'test'}, admin,
                     topics=[topic1], scopes=[topic1])
        e.emit(e.T_TEST, {'test': 'test'}, admin,
                     topics=[topic2])
        e.emit(e.T_TEST, {'test': 'test'}, admin,
                     topics=[topic1, topic2])
        
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
        