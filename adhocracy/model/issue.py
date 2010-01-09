from datetime import datetime

from sqlalchemy import Column, Unicode, ForeignKey, Integer, or_
from sqlalchemy.orm import relation
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import meta
import filter as ifilter
from delegateable import Delegateable

class Issue(Delegateable):
    __tablename__ = 'issue'
    __mapper_args__ = {'polymorphic_identity': 'issue'}
    
    id = Column(Integer, ForeignKey('delegateable.id'), primary_key=True)
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=True)
    
    def __init__(self, instance, label, creator):
        self.init_child(instance, label, creator) 
        
    def __repr__(self):
        return u"<Issue(%s)>" % (self.id)
    
    def _get_proposals(self):
        return filter(lambda p: not p.is_deleted(), self.children)
    
    def _set_proposals(self, proposals):
        self.children = proposals
        
    proposals = property(_get_proposals, _set_proposals)
    
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
        return children

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Issue)
            q = q.filter(Issue.id==id)
            if not include_deleted:
                q = q.filter(or_(Issue.delete_time==None,
                                 Issue.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Issue.instance_id==ifilter.get_instance().id)
            return q.one()
        except NoResultFound: 
            return None 
        except MultipleResultsFound:
            return None
    
    @classmethod    
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Issue)
        q = q.filter(Issue.delete_time==None)
        if not include_deleted:
            q = q.filter(or_(Issue.delete_time==None,
                             Issue.delete_time>datetime.utcnow()))
        if instance:
            q.filter(Issue.instance==instance)
        return q.all()

Issue.comment = relation('Comment', 
                         primaryjoin="Issue.comment_id==Comment.id", 
                         foreign_keys=[Issue.comment_id], 
                         uselist=False)