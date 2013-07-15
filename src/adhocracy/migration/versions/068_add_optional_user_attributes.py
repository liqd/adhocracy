from sqlalchemy import MetaData, Table, Column

from adhocracy.model.core import JSONEncodedDict
from adhocracy.model.core import MutationDict


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    table = Table('user', meta, autoload=True)
    col = Column('optional_attributes',
                 MutationDict.as_mutable(JSONEncodedDict))
    col.create(table)
