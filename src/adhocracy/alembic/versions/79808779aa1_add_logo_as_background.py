"""add_logo_as_background

Revision ID: 79808779aa1
Revises: 3bbf46ecc286
Create Date: 2014-03-11 14:29:26.115844

"""

# revision identifiers, used by Alembic.
revision = '79808779aa1'
down_revision = '3bbf46ecc286'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('instance', sa.Column('logo_as_background', sa.Boolean(),
                  nullable=True))


def downgrade():
    op.drop_column('instance', 'logo_as_background')
