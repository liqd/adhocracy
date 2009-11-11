import random 
    
from sqlalchemy import Table, Column, Integer, Unicode, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import meta
import filter
from meta import Base
from user import User

category_graph = Table('category_graph', Base.metadata,
    Column('parent_id', Unicode(10), ForeignKey('delegateable.id')),
    Column('child_id', Unicode(10), ForeignKey('delegateable.id'))
    )

class Delegateable(Base):
    PK_LENGTH = 5
    PK_ALPHABET = "abcdefgehijklmnopqrstuvwxyz0123456789"
    
    __tablename__ = 'delegateable'
    
    id = Column(Unicode(10), primary_key=True)
    label = Column(Unicode(255), nullable=False)
    delgateable_type = Column('type', String(50))
    
    create_time = Column(DateTime, default=func.now())
    access_time = Column(DateTime, default=func.now(), onupdate=func.now())
    delete_time = Column(DateTime, nullable=True)
    
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relation(User, 
        primaryjoin="Delegateable.creator_id==User.id", 
        backref=backref('delegateables', cascade='delete'))
    
    instance_id = Column(Integer, ForeignKey('instance.id'), nullable=False)
    instance = relation('Instance', 
        primaryjoin="Delegateable.instance_id==Instance.id", 
        backref=backref('delegateables', cascade='delete'))
    
    __mapper_args__ = {'polymorphic_on': delgateable_type,
                       'extension': Base.__mapper_args__.get('extension')}
    
    def __init__(self):
        raise Exception("Make a category or a motion instead!")
        
    def init_child(self, instance, label, creator):
        self.instance = instance
        self.id = self.make_key()
        self.label = label
        self.creator = creator
    
    def __repr__(self):
        return u"<Delegateable(%s,%s)>" % (self.id, self.instance.key)
    
    def __hash__(self):
        return int(self.id, len(Delegateable.PK_ALPHABET) - 1)
        
    def is_super(self, delegateable):
        if delegateable in self.children:
            return True
        for child in self.children:
            r = child.is_super(delegateable)
            if r:
                return True
        return False
        
    def is_sub(self, delegateable):
        return delegateable.is_super(self)
    
    @classmethod
    def find(cls, id, instance_filter=True):
        id = unicode(id.upper())
        try:
            q = meta.Session.query(Delegateable)
            q = q.filter(Delegateable.id==id)
            q = q.filter(Delegateable.delete_time==None)
            if filter.has_instance() and instance_filter:
                q = q.filter(Delegateable.instance_id==filter.get_instance().id)
            return q.one()
        except: 
            return None
        
    def _index_id(self):
        return self.id.upper()
    
    @staticmethod
    def make_key():
        """
        Generate an alphabet-based unique key for a Delegateable.
        Time needed for this grows as key space becomes less sparse.
        """
        while True:
            candidate = u''.join(random.sample(Delegateable.PK_ALPHABET, Delegateable.PK_LENGTH)).upper()
            try: 
                meta.Session.query(Delegateable).filter(Delegateable.id==candidate).one()
            except NoResultFound:
                return candidate
            except MultipleResultsFound:
                pass

Delegateable.__mapper__.add_property('parents', relation(Delegateable, lazy=False, secondary=category_graph, 
    primaryjoin=Delegateable.__table__.c.id == category_graph.c.parent_id,
    secondaryjoin=category_graph.c.child_id == Delegateable.__table__.c.id))
    
Delegateable.__mapper__.add_property('children', relation(Delegateable, lazy=False, secondary=category_graph, 
    primaryjoin=Delegateable.__table__.c.id == category_graph.c.child_id,
    secondaryjoin=category_graph.c.parent_id == Delegateable.__table__.c.id))