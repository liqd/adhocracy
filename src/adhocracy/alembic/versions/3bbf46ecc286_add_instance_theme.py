"""empty message

Revision ID: 3bbf46ecc286
Revises: 27af318320bd
Create Date: 2014-03-10 16:56:37.528652

"""

# revision identifiers, used by Alembic.
revision = '3bbf46ecc286'
down_revision = '27af318320bd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('instance', sa.Column('theme', sa.Unicode(), nullable=True))


def downgrade():
    op.drop_column('instance', 'theme')
