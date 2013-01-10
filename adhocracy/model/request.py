import hashlib
import os
import logging
from datetime import datetime

from babel import Locale

from pylons import config

from sqlalchemy import Table, Column, func, or_
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText
from sqlalchemy.orm import eagerload_all

from adhocracy.model import meta
from adhocracy.model import instance_filter as ifilter
from adhocracy.model.instance import Instance

log = logging.getLogger(__name__)

request_table = Table('stats', meta.data,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, default=0),
    Column('cookies', UnicodeText()),
    Column('remote_ip_address', Unicode(15)),
    Column('useragent', UnicodeText()),
    Column('request_url', UnicodeText()),
    )

class Request(meta.Indexable):
    IMPORT_MARKER = 'i__'

    def __init__(self, user_id, cookies, remote_ip_address, useragent, request_url):
        self.user_id = user_id
        self.cookies = cookies 
        self.remote_ip_address = remote_ip_address
        self.useragent = useragent
        self.request_url = request_url
