from datetime import datetime
import logging
from itertools import count

from sqlalchemy import Table, Column, Boolean, Integer, Unicode, ForeignKey, DateTime, func, or_, not_
from sqlalchemy.orm import relation, backref

import meta
from delegateable import Delegateable
import instance_filter as ifilter

log = logging.getLogger(__name__)


page_table = Table('page', meta.data,                      
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode)
    )


class Page(Delegateable):
    
    DOCUMENT = u"document"
    DESCRIPTION = u"description"
    NORM = u"norm"
    
    FUNCTIONS = [DOCUMENT, DESCRIPTION, NORM]
    PARENT_FUNCTIONS = [DOCUMENT, NORM]
    WITH_VARIANTS = [NORM] #[DESCRIPTION, NORM]
    LISTED = [DOCUMENT, NORM]
    
    def __init__(self, instance, alias, creator, function):
        self.init_child(instance, alias, creator)
        self.function = function
    
    
    @property
    def selections(self):
        return [s for s in self._selections if not s.is_deleted()]
    
    
    @classmethod
    def find_fuzzy(cls, id, instance_filter=True, include_deleted=False):
        page = cls.find(id, instance_filter=instance_filter, include_deleted=include_deleted)
        if page is None:
            from text import Text
            q = meta.Session.query(Page)
            q = q.join(Text)
            q = q.filter(Text.title.like(id))
            if not include_deleted:
                q = q.filter(or_(Page.delete_time==None,
                                 Page.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Page.instance==ifilter.get_instance())
            q = q.order_by(Text.create_time.asc())
            page = q.limit(1).first()
        return page
    
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Page)
            try:
                id = int(id)
                q = q.filter(Page.id==id)
            except ValueError:
                #from adhocracy.lib.text import title2alias
                q = q.filter(Page.label==id)
            if not include_deleted:
                q = q.filter(or_(Page.delete_time==None,
                                 Page.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Page.instance==ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    
    @classmethod       
    def _all_query(cls, instance=None, functions=[], exclude=[], 
                   include_deleted=False, include_unlisted=False):
        q = meta.Session.query(Page)
        if not include_deleted:
            q = q.filter(or_(Page.delete_time==None,
                             Page.delete_time>datetime.utcnow()))
        if functions is not None:
            q = q.filter(Page.function.in_(functions))
        if instance is not None:
            q = q.filter(Page.instance==instance)
        q = q.filter(not_(Page.id.in_([p.id for p in exclude])))
        return q 


    @classmethod
    def all(cls, **kwargs): 
        return cls._all_query(**kwargs).all()
        
    @classmethod  
    def all_roots(cls, function):
        q = meta.Session.query(Page)
        q = q.filter(or_(Page.delete_time==None,
                         Page.delete_time>datetime.utcnow()))
        q = q.filter(Page.function==function)
        if ifilter.has_instance():
            q = q.filter(Page.instance==ifilter.get_instance())
        return q.all()
    
    @classmethod 
    def count(cls, **kwargs):
        return cls._all_query(**kwargs).count()
    
    
    #@classmethod
    #def free_label(cls, title):
    #    from adhocracy.lib.text import title2alias
    #    label = title2alias(title)
    #    for i in count(0):
    #        if i == 0: test = label
    #        else: test = label + str(i)
    #        page = Page.find(test)
    #        if page is None: 
    #            return test
    
    
    @classmethod
    def create(cls, instance, title, text, creator, function=DOCUMENT, tags=None):
        from adhocracy.lib.text import title2alias
        from text import Text
        from tagging import Tagging
        if function not in Page.FUNCTIONS:
            raise AttributeError("Invalid page function type")
        label = title2alias(title)
        page = Page(instance, label, creator, function)
        meta.Session.add(page)
        meta.Session.flush()
        _text = Text(page, Text.HEAD, creator, title, text)
        
        if tags is not None:
            page.taggings = Tagging.create_all(page, tags, creator)
        
        return page
        
        
    def establish_variant(self, variant, user):
        for selection in self.selections: 
            selection.make_variant_poll(variant, user)
    
    
    def variant_polls(self, variant):
        polls = [s.variant_poll(variant) for s in self.selections]
        polls = [p for p in polls if p is not None]
        return polls
        
    
    def variant_tally(self, variant):
        from tally import Tally
        polls = self.variant_polls(variant)
        return Tally.combine_polls(polls)
    
    
    def variant_tallies(self):
        return [self.variant_tally(v) for v in self.variants]
    
    
    @property
    def proposal(self):
        if self.function == Page.DESCRIPTION:
            return self._proposal[-1]
        return None
    
    
    @property
    def subpages(self):
        return [c for c in self.children if isinstance(c, Page) and \
                c.function in self.LISTED and not c.is_deleted()]
    
    
    @property 
    def has_variants(self):
        return self.function in Page.WITH_VARIANTS
    
    
    @property
    def variants(self):
        from text import Text
        if not self.has_variants:
            return [Text.HEAD]
        return list(set([t.variant for t in self.texts]))

        
    def variant_head(self, variant):
        for text in self.texts:
            if text.variant == variant:
                return text
        return None
    
        
    def variant_at(self, variant, at_time):
        for text in self.variant_history(variant):
            if text.create_time <= at_time:
                return text
        return None
            
    
    def variant_history(self, variant):
        head = self.variant_head(variant)
        if head:
            return head.history
        return []
        
        
    def variant_comments(self, variant):
        return [c for c in self.comments if (not c.is_deleted()) and c.variant == variant]
    
    
    @property
    def heads(self):
        from text import Text
        if not has_variants:
            return [self.variant_head(Text.HEAD)]
        return [self.variant_head(h) for h in self.variants]
    
    
    @property
    def head(self):
        from text import Text
        return self.variant_head(Text.HEAD)
    
    
    @property
    def title(self):
        return self.head.title
     
    
    @property
    def full_title(self):
        from adhocracy.lib.helpers import text
        title = text.truncate(self.title, length=40, whole_word=True)
        if self.parent:
            title = self.parent.full_title + " - " + title
        return title
        
    
    def _get_parent(self):
        for parent in self.parents:
            if isinstance(parent, Page):
                return parent
        return None
        
    
    def _set_parent(self, parent):
        parents = []
        for old_parent in self.parents:
            if not isinstance(old_parent, Page):
                parents.append(old_parent)
        if parent is not None:
            parents.append(parent)
        self.parents = parents        
    
    
    parent = property(_get_parent, _set_parent)
    
    
    @property
    def changing_selections(self):
        from text import Text
        selections = []
        for selection in self.selections:
            if selection.is_deleted():
                continue
            if selection.proposal.adopted:
                continue
            if selection.selected != Text.HEAD:
                selections.append(selection)
        return selections
    
    
    def supporting_selections(self, variant):
        from text import Text
        selections = []
        for selection in self.selections:
            if selection.is_deleted():
                continue
            if selection.proposal.adopted:
                continue
            if selection.selected == variant:
                selections.append(selection)
        return selections


    #@property
    #def proposal(self):
    #    from proposal import Proposal
    #    if self.function == Page.DESCRIPTION:
    #        for parent in self.parents:
    #            if isinstance(parent, Proposal):
    #                return parent
    #    return None    
    
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        for text in self.texts:
            text.delete(delete_time=delete_time)
        for selection in self.selections:
            selection.delete(delete_time=delete_time)
        if self.delete_time is None:
            self.delete_time = delete_time
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    
    def is_mutable(self):
        if self.function == self.DESCRIPTION and self.proposal:
            return self.proposal.is_mutable()
        return True
        
    
    def user_position(self, user):
        if self.function == self.DESCRIPTION and self.proposal:
            return self.proposal.user_position(user)
        return 0
    
    
    def _index_id(self):
        return self.id
    
        
    def contributors(self):
        from user import User
        from text import Text
        q = meta.Session.query(User)
        q = q.join(Text)
        q = q.add_column(func.count(Text.id))
        q = q.filter(Text.page==self)
        q = q.group_by(User.id)
        q = q.order_by(func.count(Text.id).desc())
        cbs = super(Page, self).contributors()
        return self._join_contributors(cbs, q.all(), second_factor=2)
    
    
    def to_dict(self, text=None):
        if text is None:
            text = self.head
        from adhocracy.lib import helpers as h
        d =    dict(id=self.id,
                    url=h.entity_url(self),
                    create_time=self.create_time,
                    label=self.label,
                    title=self.title,
                    full_title=self.full_title,
                    text=text,
                    function=self.function,
                    creator=self.creator.user_name)
        if self.parent:
            d['parent'] = self.parent
        return d 
    
    
    def __repr__(self):
        return u"<Page(%s)>" % (self.id)
    
