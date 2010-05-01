from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

page_table = Table('page', meta,                      
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode)
    )

proposal_table = Table('proposal', meta,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
    Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('rate_poll_id', Integer, ForeignKey('poll.id'), nullable=True),
    Column('adopted', Boolean, default=False)
    )

selection_table = Table('selection', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime),
    Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=True)
    )

def upgrade():
    selection_table.create()
    
def downgrade():
    selection_table.drop()
