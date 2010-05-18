from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

delegateable_table = Table('delegateable', meta,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )

def upgrade():
    page_table = Table('page', meta,                      
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('has_variants', Boolean, default=True),
        Column('freeze', Boolean, default=False)
        )
    page_table.c.has_variants.drop()
    page_table.c.freeze.drop()
    function = Column('function', Unicode)
    function.create(page_table)
    u = page_table.update(values={
        'function': 'document'
        })
    migrate_engine.execute(u)
    

def downgrade():
    page_table = Table('page', meta,                      
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('function', Unicode)
        )
    has_variants = Column('has_variants', Boolean, default=True)
    has_variants.create(page_table)
    freeze = Column('freeze', Boolean, default=False)
    freeze.create(page_table)
    
