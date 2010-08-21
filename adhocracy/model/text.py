from datetime import datetime
import logging

from sqlalchemy import Table, Column, Integer, Unicode, UnicodeText, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

import meta
import instance_filter as ifilter

log = logging.getLogger(__name__)


text_table = Table('text', meta.data,                      
    Column('id', Integer, primary_key=True),
    Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('parent_id', Integer, ForeignKey('text.id'), nullable=True),
    Column('variant', Unicode(255), nullable=True),
    Column('title', Unicode(255), nullable=True),
    Column('text', UnicodeText(), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime)
    )


class Text(object):
    
    HEAD = u'HEAD'
    LINE_LENGTH = 60
    
    def __init__(self, page, variant, user, title, text):
        self.page = page
        self.variant = variant
        self.user = user
        self.title = title
        self.text = text
    
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Text)
            q = q.filter(Text.id==id)
            if not include_deleted:
                q = q.filter(or_(Text.delete_time==None,
                                 Text.delete_time>datetime.utcnow()))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None


    @classmethod
    def create(cls, page, variant, user, title, text, parent=None):
        from adhocracy.lib.text import title2alias
        if variant is None:
            if parent is not None:
                variant = parent.variant
            else:
                variant = Text.HEAD
        
        variant_is_new = False
        if not variant in page.variants:
            variant_is_new = True
        _text = Text(page, variant, user, title, text)
        if parent:
            _text.parent = parent
        meta.Session.add(_text)
        meta.Session.flush()
        if variant_is_new:
            page.establish_variant(variant, user)
        return _text
    
    
    @property
    def history(self):
        # TODO: Performance fail.
        if self.parent:
            return [self] + self.parent.history
        return [self]
    
    
    @property
    def variant_title(self):
        from pylons.i18n import _
        if self.variant == self.HEAD:
            return _("[status quo]")
        return self.variant
    
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    
    def render(self):
        from adhocracy.lib import text
        if self.page.function == self.page.NORM:
            return text.render_line_based(self)
        return text.render(self.text)
    
    @property
    def lines(self):
        from webhelpers.text import truncate
        for line in self.text.split("\n"):
            while len(line) > self.LINE_LENGTH:
                part = truncate(line, length=self.LINE_LENGTH, indicator='', whole_word=True)
                line = line[len(part):]
                line = line.lstrip()
                yield part
            yield line
    
    @property
    def has_text(self):
        return self.text is not None and len(self.text.strip()) > 0
    
    
    @property 
    def is_head(self):
        return self.variant == self.HEAD
    
    
    def _index_id(self):
        return self.id
    
    
    def to_dict(self):
        from adhocracy.lib import helpers as h
        d =    dict(id=self.id,
                    page_id=self.page.id,
                    url=h.entity_url(self),
                    create_time=self.create_time,
                    text=self.text,
                    variant=self.variant,
                    title=self.title,
                    user=self.user.user_name)
        if self.parent:
            d['parent'] = self.parent.id
        return d
    
    
    def __repr__(self):
        return u"<Text(%s, %s, %s)>" % (self.id, self.variant.encode('ascii', 'replace'), 
                                        self.user.user_name)
    
