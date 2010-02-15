from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

def upgrade():
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
        )
    adopted = Column('adopted', Boolean, default=False)
    adopted.create(proposal_table)

def downgrade():
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
        Column('adopted', Boolean, default=False)
        )
    proposal_table.c.adopted.drop()
