from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)



user_table = Table('user', meta,
    Column('id', Integer, primary_key=True),
    Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
    Column('display_name', Unicode(255), nullable=True, index=True),
    Column('bio', UnicodeText(), nullable=True),
    Column('email', Unicode(255), nullable=True, unique=False),
    Column('email_priority', Integer, default=3),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('reset_code', Unicode(255), nullable=True, unique=False),
    Column('password', Unicode(80), nullable=False),
    Column('locale', Unicode(7), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime)
    )

instance_table = Table('instance', meta,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(20), nullable=False, unique=True),
    Column('label', Unicode(255), nullable=False),
    Column('description', UnicodeText(), nullable=True),
    Column('required_majority', Float, nullable=False),
    Column('activation_delay', Integer, nullable=False),
    Column('create_time', DateTime, default=func.now()),
    Column('access_time', DateTime, default=func.now(), onupdate=func.now()),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('default_group_id', Integer, ForeignKey('group.id'), nullable=True),
    Column('allow_adopt', Boolean, default=True),       
    Column('allow_delegate', Boolean, default=True),
    Column('allow_index', Boolean, default=True),
    Column('hidden', Boolean, default=False)   
    )

page_table = Table('page', meta,                      
    Column('id', Integer, primary_key=True),
    Column('alias', Unicode(255), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=datetime.utcnow)
    )
 
 
text_table = Table('text', meta ,                      
    Column('id', Integer, primary_key=True),
    Column('page_id', Integer, ForeignKey('page.id'), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('parent_id', Integer, ForeignKey('text.id'), nullable=True),
    Column('variant', Unicode(255), nullable=True),
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
