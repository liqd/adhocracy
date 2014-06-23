"""Longer locale columns

Revision ID: 1e296c7f5e8c
Revises: 581e036204e2
Create Date: 2014-06-23 15:27:10.622251

"""

# revision identifiers, used by Alembic.
revision = '1e296c7f5e8c'
down_revision = '581e036204e2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('instance', 'locale', type_=sa.Unicode(10))
    op.alter_column('user', 'locale', type_=sa.Unicode(10))


def downgrade():
    op.alter_column('user', 'locale', type_=sa.Unicode(7))
    op.alter_column('instance', 'locale', type_=sa.Unicode(7))
