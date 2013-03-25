from sqlalchemy import Table, Column
from sqlalchemy import Unicode, UnicodeText
from adhocracy.model import meta

staticpage_table = Table(
    'staticpage', meta.data,
    Column('key', Unicode(256), primary_key=True),
    Column('lang', Unicode(7), primary_key=True),
    Column('title', UnicodeText(), nullable=True),
    Column('body', UnicodeText()),
)


class StaticPage(object):
    def __init__(self, key, lang, title, body):
        self.key = key
        self.lang = lang
        self.title = title
        self.body = body

    @classmethod
    def get(cls, key, lang):
        """ Get the specified static page or None if it cannot be found """
        q = meta.Session.query(cls)
        q = q.filter(cls.key == key, cls.lang == lang)
        return q.first()

    @classmethod
    def create(cls, key, lang, title, body):
        s = StaticPage(key, lang, title, body)
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
