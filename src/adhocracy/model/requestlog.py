import logging
from datetime import datetime
from sqlalchemy import Table, Column
from sqlalchemy import Integer, Unicode, UnicodeText, DateTime
from adhocracy.model import meta

log = logging.getLogger(__name__)

requestlog_table = Table(
    'requestlog', meta.data,
    Column('id', Integer, primary_key=True),
    Column('access_time', DateTime, default=datetime.utcnow),
    Column('ip_address', Unicode(255), nullable=True),
    Column('request_url', UnicodeText()),
    Column('cookies', UnicodeText(), nullable=True),
    Column('user_agent', UnicodeText(), nullable=True),
    Column('referer', UnicodeText(), nullable=True),
)


class RequestLog(object):
    def __init__(self, access_time, ip_address, request_url, cookies,
                 user_agent, referer):
        self.id = None
        self.access_time = access_time
        self.ip_address = ip_address
        self.request_url = request_url
        self.cookies = cookies
        self.user_agent = user_agent
        self.referer = referer

    @classmethod
    def create(cls, ip_address, request_url, cookies, user_agent, referer):
        entry = cls(datetime.utcnow(), ip_address, request_url, cookies,
                    user_agent, referer)
        meta.Session.add(entry)
        return entry
