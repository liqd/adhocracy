from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData(migrate_engine)

proposal_table = Table('proposal', meta,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
    )

poll_table = Table('poll', meta,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('begin_user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)   
    )

dependency_table = Table('dependency', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False),
    Column('requirement_id', Integer, ForeignKey('proposal.id'), nullable=False)
    )


def upgrade():
    dependency_table.drop()

def downgrade():
    dependency_table.create()
