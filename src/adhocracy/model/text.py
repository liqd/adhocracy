from datetime import datetime
import logging

from pylons.i18n import _
from sqlalchemy import Column, ForeignKey, Table, or_
from sqlalchemy import Boolean, Integer, Unicode, UnicodeText, DateTime

import meta

log = logging.getLogger(__name__)


text_table = Table(
    'text', meta.data,
    Column('id', Integer, primary_key=True),
    Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('child_id', Integer, ForeignKey('text.id'), nullable=True),
    Column('variant', Unicode(255), nullable=True),
    Column('title', Unicode(255), nullable=True),
    Column('text', UnicodeText(), nullable=True),
    Column('wiki', Boolean, default=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime)
)


class Text(object):

    HEAD = u'HEAD'
    LINE_LENGTH = 60

    def __init__(self, page, variant, user, title, text, wiki=False):
        self.page = page
        self.variant = variant
        self.user = user
        self.title = title
        self.text = text
        self.wiki = wiki

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Text)
            q = q.filter(Text.id == id)
            if not include_deleted:
                q = q.filter(or_(Text.delete_time == None,
                                 Text.delete_time > datetime.utcnow()))
            return q.first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    @classmethod
    def create(cls, page, variant, user, title, text, parent=None, wiki=False):
        if variant is None:
            if parent is not None:
                variant = parent.variant
            else:
                variant = Text.HEAD

        variant_is_new = variant not in page.variants
        _text = Text(page, variant, user, title, text, wiki)
        if parent:
            _text.parent = parent
        meta.Session.add(_text)
        meta.Session.flush()
        if variant_is_new:
            page.establish_variant(variant, user)
        return _text

    def history_q(self, include_deleted=False):
        texts_q = meta.Session.query(Text).filter(
            Text.page_id == self.page_id, Text.variant == self.variant)
        if not include_deleted:
            texts_q = texts_q.filter(
                or_(Text.delete_time == None,  # noqa
                    Text.delete_time > datetime.now()))
        return texts_q

    @property
    def history(self, include_deleted=False):
        return self.history_q().all()

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return ((self.delete_time is not None) and
                self.delete_time <= at_time)

    def valid_parent(self):
        parent = self.parent
        if parent is not None and parent.is_deleted():
            return parent.valid_parent()
        else:
            return parent

    def valid_child(self):
        child = self.child
        if child is not None and child.is_deleted():
            return child.valid_child()
        else:
            return child

    def render(self):
        from adhocracy.lib import text
        if self.page.function == self.page.NORM:
            return text.render_line_based(self)
        return text.render(self.text)

    @property
    def lines(self):
        from webhelpers.text import truncate
        if self.text is None:
            return
        for line in self.text.strip().split("\n"):
            while len(line.rstrip()) > self.LINE_LENGTH:
                part = truncate(line, length=self.LINE_LENGTH, indicator='',
                                whole_word=True)
                line = line[len(part):]
                line = line.lstrip()
                yield part
            yield line

    @property
    def lines_text(self):
        return '\n'.join(self.lines)

    @property
    def has_text(self):
        return self.text is not None and len(self.text.strip()) > 0

    @property
    def variant_name(self):
        if self.is_head:
            return _("Status Quo")
        return self.variant

    @property
    def variant_html(self):
        import cgi
        variant_name = cgi.escape(self.variant_name)
        if self.is_head:
            return "<em class='varname status_quo'>%s</em>" % variant_name
        return"<code class='varname'>%s</code>" % variant_name

    @property
    def is_head(self):
        return self.variant == self.HEAD

    def to_dict(self):
        from adhocracy.lib import helpers as h
        d = dict(id=self.id,
                 page_id=self.page.id,
                 url=h.entity_url(self),
                 create_time=self.create_time,
                 text=self.text,
                 variant=self.variant,
                 title=self.title,
                 wiki=self.wiki,
                 user=self.user.user_name)
        if self.parent:
            d['parent'] = self.parent.id
        return d

    def __repr__(self):
        variant_str = self.variant.encode('ascii', 'replace')
        return u"<Text(%s, %s, %s)>" % (self.id, variant_str,
                                        self.user.user_name)
