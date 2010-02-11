from datetime import datetime
import logging

from sqlalchemy import Table, Column, Unicode, ForeignKey, Integer, or_
from sqlalchemy.orm import relation, mapper
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import meta
import filter as ifilter
from delegateable import Delegateable

log = logging.getLogger(__name__)

issue_table = Table('issue', meta.data,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
    )

class Issue(Delegateable):
    
    def __init__(self, instance, label, creator):
        self.init_child(instance, label, creator) 
    
    def _get_proposals(self):
        return filter(lambda p: not p.is_deleted(), self.children)
    
    def _set_proposals(self, proposals):
        self.children = proposals
        
    proposals = property(_get_proposals, _set_proposals)
    
    
    def search_children(self, recurse=False, cls=Delegateable): 
        """ Get all child elements of type "cls". Uses DFS. """
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
            q = q.filter(Issue.id==int(id))
            if not include_deleted:
                q = q.filter(or_(Issue.delete_time==None,
                                 Issue.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Issue.instance_id==ifilter.get_instance().id)
            return q.one()
        except Exception, e: 
            log.warn("find(%s): %s" % (id, e))
            return None
    
    
    @classmethod
    def find_by_creator(cls, user, instance_filter=True):
        q = meta.Session.query(Issue)
        q = q.filter(Issue.creator==user)
        q = q.filter(or_(Issue.delete_time==None,
                         Issue.delete_time>datetime.utcnow()))
        if ifilter.has_instance() and instance_filter:
            q = q.filter(Issue.instance_id==ifilter.get_instance().id)
        return q.all()
    
    
    @classmethod    
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Issue)
        if not include_deleted:
            q = q.filter(or_(Issue.delete_time==None,
                             Issue.delete_time>datetime.utcnow()))
        if instance is not None:
            q = q.filter(Issue.instance==instance)
        return q.all()
    
    
    def comment_count(self, recurse=True):
        count = len([c for c in self.comments if not c.is_deleted()])
        if self.comment and not self.comment.is_deleted():
            count -= 1
        if recurse:
            count += sum([p.comment_count() for p in self.proposals])
        return count
    
    
    @classmethod
    def create(cls, instance, label, user):
        issue = Issue(instance, label, user)
        meta.Session.add(issue)
        meta.Session.flush()        
        return issue
    
    
    def to_dict(self):
        d = super(Issue, self).to_dict()
        if self.comment_id:
            d['comment'] = self.comment_id
        d['proposals'] = map(lambda p: p.id, self.proposals)
        return d
        
    def __repr__(self):
        return u"<Issue(%s)>" % (self.id)
    