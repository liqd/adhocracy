from sqlalchemy import MetaData, Column, Table, ForeignKey, Integer, Unicode


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    badge_table = Table('badge', meta, autoload=True)

    treatment_table = Table(
        'treatment', meta,
        Column('id', Integer, primary_key=True),
        Column('key', Unicode(40), nullable=False, unique=True),
        Column('variant_count', Integer(), nullable=False),
    )

    treatment_source_badges_table = Table(
        'treatment_source_badges', meta,
        Column('treatment_id', Integer,
               ForeignKey('treatment.id', ondelete='CASCADE')),
        Column('badge_id', Integer,
               ForeignKey('badge.id', ondelete='CASCADE')),
    )

    treatment_table.create()
    treatment_source_badges_table.create()
