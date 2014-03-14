"""Added velruse table

Revision ID: 486aab29697a
Revises: 60dd2bc41b
Create Date: 2014-03-11 10:58:58.788954

"""

# revision identifiers, used by Alembic.
revision = '486aab29697a'
down_revision = '60dd2bc41b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'velruse',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=True),
        sa.Column('delete_time', sa.DateTime(), nullable=True),
        sa.Column('domain', sa.Unicode(length=255), nullable=False),
        sa.Column('domain_user', sa.Unicode(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain', 'domain_user',
                            name='unique_velruse_user')
    )
    op.create_index('ix_velruse_domain', 'velruse', ['domain'],
                    unique=False)
    op.create_index('ix_velruse_domain_user', 'velruse', ['domain_user'],
                    unique=False)


def downgrade():
    op.drop_index('ix_velruse_domain_user', table_name='velruse')
    op.drop_index('ix_velruse_domain', table_name='velruse')
    op.drop_table('velruse')
