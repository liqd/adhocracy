from sqlalchemy import MetaData, Table


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    message_table = Table('message', meta, autoload=True)

    message_table.c.sender_email.drop()
    message_table.c.sender_name.drop()
    message_table.c.include_footer.drop()

    instance_id = Column('instance_id', Integer, ForeignKey('instance.id'),
                         nullable=True)
    instance_id.create(message_table)


def downgrade(migrate_engine):
    raise NotImplementedError()
