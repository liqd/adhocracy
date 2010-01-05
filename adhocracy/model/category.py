from sqlalchemy import Column, Unicode, UnicodeText, ForeignKey, Integer
import meta
import filter
from delegateable import Delegateable
from issue import Issue

class Category(Delegateable):
    __tablename__ = 'category'
    __mapper_args__ = {'polymorphic_identity': 'category'}
    
    id = Column(Integer, ForeignKey('delegateable.id'), primary_key=True)
    description = Column(UnicodeText(), nullable=True)
    
    def __init__(self, instance, label, creator):
        self.init_child(instance, label, creator) 
        
    def __repr__(self):
        return u"<Category(%s)>" % (self.id)
        
    def search_children(self, recurse=False, cls=Delegateable): 
        """
        Get all child elements of type "cls". Uses DFS. 
        """
        children = []
        for child in self.children:
            if child.delete_time: 
                continue
            if isinstance(child, cls):
                children.append(child)
            if recurse and isinstance(child, Category):
                children = children + child.search_children(recurse=True, cls=cls)
            if recurse and isinstance(child, Issue):
                children = children + child.search_children(cls=cls)
        return children

    @classmethod
    def find(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(Category)
            q = q.filter(Category.id==id)
            q = q.filter(Category.delete_time==None)
            if filter.has_instance() and instance_filter:
                q = q.filter(Category.instance_id==filter.get_instance().id)
            return q.one()
        except: 
            return None 