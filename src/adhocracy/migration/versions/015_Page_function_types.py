from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData()

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

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    page_table = Table('page', meta,                      
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('has_variants', Boolean, default=True),
        Column('freeze', Boolean, default=False)
        )
    page_table.c.has_variants.drop()
    page_table.c.freeze.drop()
    #function = Column('function', Unicode)
    #function.create(page_table)
    #u = page_table.update(values={
    #    'function': 'document'
    #    })
    print "WARNING ---- THERE IS A NON-WORKING MIGRATION PART ---- "
    print "CREATE A NEW function COLUMN ON THE page TABLE "
    #migrate_engine.execute(u)
    

def downgrade(migrate_engine):
    raise NotImplementedError()
    
