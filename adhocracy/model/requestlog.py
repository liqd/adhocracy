import logging
from datetime import datetime
from sqlalchemy import Table, Column
from sqlalchemy import Integer, Unicode, UnicodeText, DateTime
from adhocracy.model import meta

log = logging.getLogger(__name__)

requestlog_table = Table('requestlog', meta.data,
    Column('id', Integer, primary_key=True),
    Column('access_time', DateTime),
    Column('ip_address', Unicode(255), nullable=True),
    Column('request_url', UnicodeText()),
    Column('cookies', UnicodeText(), nullable=True),
    Column('user_agent', UnicodeText(), nullable=True),
)

class RequestLog(object):
    def __init__(self, ip_address, request_url, user_agent, access_time):
        self.id = None
        self.access_time = access_time
        self.ip_address = ip_address
        self.request_url = request_url
        self.cookies = cookies
        self.user_agent = user_agent

    @classmethod
    def create(cls, ip_address, request_url, cookies, user_agent):
        entry = cls(ip_address, request_url, cookies, user_agent, access_time=datetime.utcnow())
        meta.Session.add(entry)
        return entry
