from datetime import datetime

import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import DateTime, Integer, Unicode
import meta

log = logging.getLogger(__name__)


shibboleth_table = Table(
    'shibboleth', meta.data,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('persistent_id', Unicode(1024), nullable=False, unique=True,
           index=True),
)


class Shibboleth(object):

    def __init__(self, persistent_id, user):
        self.persistent_id = persistent_id
        self.user = user
