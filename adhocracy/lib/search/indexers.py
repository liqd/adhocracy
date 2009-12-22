import logging
from datetime import datetime

from lucene import Field, Document, Term

from adhocracy import model
from adhocracy.model import hooks
from .. import text 

import index
import entityrefs

class Indexer(object):
    
    def __init__(self, entity, doc=None, boost=1.0):
        self.entity = entity
        self.boost = boost
        self._doc = doc
        
    def _get_doc(self):
        if not self._doc:
            self._doc = Document()
            self._doc.add(Field("id", str(self.entity._index_id()), 
                                Field.Store.YES, Field.Index.NOT_ANALYZED ))
            self._doc.add(Field("ref", entityrefs.to_ref(self.entity), 
                                Field.Store.YES, Field.Index.NOT_ANALYZED ))
            self._doc.add(Field("type", entityrefs.entity_type(self.entity),
                                Field.Store.YES, Field.Index.NOT_ANALYZED ))
            self._doc.add(Field("entity", "true",
                                Field.Store.YES, Field.Index.NOT_ANALYZED ))
        return self._doc
    
    doc = property(_get_doc)
    
    def include_date(self, key, ts, boost):
        if not ts:
            ts = datetime.now()  # for newly persited entities
        ts_str = ts.strftime('%Y%m%d')
        f = Field(key, ts_str, Field.Store.NO,
                  Field.Index.NOT_ANALYZED )
        f.setBoost(boost)  
        self.doc.add(f)  
    
    def delete(self):
        index.delete_document(Term("ref", entityrefs.to_ref(self.entity)))
    
    def add(self):
        self.serialize()
        index.write_document(self.doc)
        
        
class UserIndexer(Indexer):
    
    def serialize(self, partial=False):
        f = Field("user", self.entity.user_name, 
                  Field.Store.NO, Field.Index.ANALYZED )
        f.setBoost(self.boost)
        self.doc.add(f)
        
        if self.entity.display_name:
            f = Field("user", self.entity.display_name, 
                      Field.Store.NO, Field.Index.ANALYZED )
            f.setBoost(self.boost)
            self.doc.add(f)
        if not partial:
            self.include_date("create_time", self.entity.create_time, 
                              self.boost * 0.5)
            if self.entity.bio:
                f = Field("description", text.plain(self.entity.bio), 
                          Field.Store.NO, Field.Index.ANALYZED )
                f.setBoost(self.boost * 0.5)
                self.doc.add(f)
            
            for instance in self.entity.instances:
                f = Field("instance", instance.key, 
                          Field.Store.YES, Field.Index.NOT_ANALYZED )
                f.setBoost(self.boost)
                self.doc.add(f) 

class CommentIndexer(Indexer):
    
    def serialize(self, partial=False, depth=3):
        if self.entity.delete_time or self.entity.topic.delete_time:
            self.delete()
            return 
        
        if not self.entity.canonical:
            self.boost = self.boost * 0.9
            
        creator = UserIndexer(self.entity.creator, doc=self.doc, 
                              boost=self.boost*0.5)
        creator.serialize(partial=True)
        
        f = Field("canonical", "true" if self.entity.canonical else "false", 
                  Field.Store.NO, Field.Index.NOT_ANALYZED )
        f.setBoost(self.boost * 0.1)
        self.doc.add(f)
        
        for revision in self.entity.revisions[:depth]:
            self.include_date("create_time", self.entity.create_time, 
                              self.boost * 0.5)
            
            f = Field("description", text.plain(revision.text), 
                  Field.Store.NO, Field.Index.ANALYZED )
            f.setBoost(self.boost * 0.9)
            self.doc.add(f)
            
            user = UserIndexer(revision.user, doc=self.doc, 
                              boost=self.boost*0.5)
            user.serialize(partial=True)
        
        if not partial:
            didx = DelegateableIndexer(self.entity.topic, doc=self.doc,
                                       boost=self.boost * 0.5)
            didx.serialize(partial=True)
      
class DelegateableIndexer(Indexer):
    
    def serialize(self, partial=False):
        # funny dispatch ftw! 
        if self.entity.delete_time:
            self.delete()
            return
        
        if isinstance(self.entity, model.Motion):
            midx = MotionIndexer(self.entity, doc=self.doc, 
                                 boost=self.boost)
            midx.serialize(partial=partial)
        elif isinstance(self.entity, model.Issue):
            iidx = IssueIndexer(self.entity, doc=self.doc, 
                                boost=self.boost)
            iidx.serialize(partial=partial)
        elif isinstance(self.entity, model.Category):
            cidx = CategoryIndexer(self.entity, doc=self.doc, 
                                   boost=self.boost)
            cidx.serialize(partial=partial)
        else:
            self.serialize_delegateable(partial=partial)
    
    def serialize_delegateable(self, partial=False):
        f = Field("label", self.entity.label, 
                  Field.Store.NO, Field.Index.ANALYZED )
        f.setBoost(self.boost * 2.0)
        self.doc.add(f)
        
        f = Field("instance", self.entity.instance.key, 
                  Field.Store.YES, Field.Index.NOT_ANALYZED )
        f.setBoost(self.boost)
        self.doc.add(f)
        
        creator = UserIndexer(self.entity.creator, doc=self.doc, 
                              boost=self.boost*0.9)
        creator.serialize(partial=True)
        
        if not partial:
            for comment in self.entity.comments:
                cidx = CommentIndexer(comment, doc=self.doc, boost=0.8)
                cidx.serialize(partial=True)
            
class CategoryIndexer(DelegateableIndexer):
    
    def serialize(self, partial=False):
        if self.entity.instance.root == self.entity:
            return
        if self.entity.description:
            f = Field("description", text.plain(self.entity.description), 
                      Field.Store.NO, Field.Index.ANALYZED )
            f.setBoost(self.boost * 1.0)
            self.doc.add(f)
        
        self.serialize_delegateable(partial=partial)
        
class IssueIndexer(DelegateableIndexer):
    
    def serialize(self, partial=False):
        self.serialize_delegateable(partial=partial)
        
        if not partial:
            for motion in self.entity.children:
                midx = MotionIndexer(motion, doc=self.doc,
                                     boost=self.boost * 0.7)
                midx.serialize(partial=True)
           
class MotionIndexer(DelegateableIndexer):
    
    def serialize(self, partial=False):
        self.serialize_delegateable(partial=partial)    
        
        if not partial and self.entity.issue:
            iidx = IssueIndexer(self.entity.issue, doc=self.doc, 
                                boost=self.boost * 0.7)
            iidx.serialize(partial=True)
        
def insert(indexer_cls):
    def f(entity):
        #model.meta.Session.refresh(entity)
        indexer = indexer_cls(entity)
        indexer.add()
    return f

def update(indexer_cls):
    def f(entity):
        #model.meta.Session.refresh(entity)
        indexer = indexer_cls(entity)
        indexer.delete()
        indexer.add()
    return f

def delete(indexer_cls):
    def f(entity):
        indexer = indexer_cls(entity)
        indexer.delete()
    return f

def register_indexer(cls, indexer_cls):
    hooks.patch(cls, hooks.POSTINSERT, insert(indexer_cls))
    hooks.patch(cls, hooks.POSTUPDATE, update(indexer_cls))
    hooks.patch(cls, hooks.POSTDELETE, delete(indexer_cls))

