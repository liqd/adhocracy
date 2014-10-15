import logging

from sqlalchemy import Table, Column
from sqlalchemy import Unicode, UnicodeText

from adhocracy.model import meta

log = logging.getLogger(__name__)


staticpage_table = Table(
    'staticpage', meta.data,
    Column('key', Unicode(256), primary_key=True),
    Column('lang', Unicode(7), primary_key=True),
    Column('title', UnicodeText(), nullable=True),
    Column('body', UnicodeText()),
)


class StaticPageBase(object):

    private = False
    nav = u''
    description = u''
    column_right = u''
    css_classes = []
    redirect_url = u''

    def __init__(self, key, lang, body, title, private=False,
                 nav=u'', description=u'', column_right=u'', css_classes=[],
                 redirect_url=u''):
        self.key = key
        self.lang = lang
        self.title = title
        self.body = body
        self.private = private
        self.nav = nav
        self.description = description
        self.column_right = column_right
        self.css_classes = css_classes
        self.redirect_url = redirect_url

    @staticmethod
    def get(key, lang):
        raise NotImplementedError()

    def commit(self):
        """ Persist changes to this object. """
        raise NotImplementedError()

    @staticmethod
    def all():
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    @staticmethod
    def create(key, lang, title, body):
        raise NotImplementedError()

    @staticmethod
    def is_editable():
        return False

    def require_permission(self):
        """
        Backends can add additional permission checks.
        """
        if self.private:
            from adhocracy.lib.auth import require
            require.perm('static.show_private')


class StaticPage(StaticPageBase):

    @classmethod
    def get(cls, key, languages):
        """ Get the specified static page or None if it cannot be found """
        for lang in languages:
            q = meta.Session.query(cls)
            q = q.filter(cls.key == key, cls.lang == lang)
            if q.count():
                return q.first()
        return None

    @classmethod
    def create(cls, key, lang, title, body):
        s = StaticPage(key, lang, body, title)
        meta.Session.add(s)
        meta.Session.commit()
        return s

    @classmethod
    def all(cls):
        q = meta.Session.query(cls)
        return q.all()

    @staticmethod
    def is_editable():
        return True

    def commit(self):
        """ Persist changes to this object (interface for disk + database) """
        meta.Session.add(self)
        meta.Session.commit()

    def require_permission(self):
        return False
