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
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True)
        )
    has_variants = Column('has_variants', Boolean, default=True)
    has_variants.create(page_table)
    freeze = Column('freeze', Boolean, default=False)
    freeze.create(page_table)
    

def downgrade():
    page_table.c.has_variants.drop()
    page_table.c.freeze.drop()
