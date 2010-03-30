from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

page_table = Table('page', meta,                      
    Column('id', Integer, primary_key=True),
    Column('alias', Unicode(255), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=datetime.utcnow)
    )
  
text_table = Table('text', meta.data,                      
    Column('id', Integer, primary_key=True),
    Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('variant', Unicode(255), nullable=False),
    Column('short_title', Unicode(255), nullable=False),
    Column('title', Unicode(255), nullable=True),
    Column('text', UnicodeText(), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime)
    )


def upgrade():
    page_table.create()
    text_table.create()

def downgrade():
    text_table.drop()
    page_table.drop()
