from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
        )
    adopted = Column('adopted', Boolean, default=False)
    adopted.create(proposal_table)

def downgrade(migrate_engine):
    raise NotImplementedError()
