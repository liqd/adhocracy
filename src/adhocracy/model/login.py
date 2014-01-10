import hashlib
import os
import logging
import datetime

from babel import Locale
from pylons import config
from pylons.i18n import _

from sqlalchemy import Table, Column
from sqlalchemy import DateTime, Integer, Unicode, UnicodeText

from adhocracy.model import meta
import logging
import meta
from sqlalchemy import MetaData


login_table = Table(
    'loginlog', meta.data,
    Column('id', Integer, primary_key=True),
    Column('access_time', DateTime),
    Column('ip_address', Unicode(255), nullable=True),
    Column('user', UnicodeText()),
    Column('success', UnicodeText())
)


class Login(meta.Indexable):

    def __init__(self, access_time, ip_adress, user, success):
        self.access_time = datetime.datetime.utcnow()
        self.ip_address = ip_adress
        self.user = user
        self.success = success

    # def count returns amount of unsuccessful logins of past hour
    @classmethod
    def count_logs(cls, user):
        q = meta.Session.query(cls)
        q = q.filter(cls.user == user, cls.success == 'no',
                     ((datetime.datetime.utcnow()
                      - datetime.timedelta(hours=1)) < cls.access_time))
        return q.count()

    @classmethod
    def create(cls, access_time, ip_adress, user, success):
        l = Login(access_time, ip_adress, user, success)
        meta.Session.add(l)
        meta.Session.flush()
        meta.Session.commit()
        return l
