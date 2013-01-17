import logging
from datetime import datetime

from sqlalchemy import Table, Column, func, or_
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

from adhocracy.model import meta
from adhocracy.model import instance_filter as ifilter

log = logging.getLogger(__name__)

request_table = Table('request', meta.data,
    Column('id', Integer, primary_key=True),
    Column('cookies', UnicodeText(), nullable=True),
    Column('remote_ip_address', Unicode(255)),
    Column('useragent', UnicodeText(), nullable=True),
    Column('request_url', UnicodeText()),
    )

class Request(object):

    def __init__(self, cookies, remote_ip_address, useragent, request_url):
        self.id = None
        self.cookies = cookies 
        self.remote_ip_address = remote_ip_address
        self.useragent = useragent
        self.request_url = request_url
    
    def SaveRequest(self):
        request = Request(self.cookies, self.remote_ip_address, self.useragent, self.request_url)
        meta.Session.add(request)
        meta.Session.commit()
