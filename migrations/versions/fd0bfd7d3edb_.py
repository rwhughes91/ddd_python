"""empty message

Revision ID: fd0bfd7d3edb
Revises: 313ffab7ab2c
Create Date: 2021-09-25 12:26:01.949981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd0bfd7d3edb'
down_revision = '313ffab7ab2c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('version_number', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'version_number')
    # ### end Alembic commands ###