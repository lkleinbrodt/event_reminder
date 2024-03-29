"""first

Revision ID: ffb95ef098d0
Revises: 
Create Date: 2024-01-21 12:49:27.254188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffb95ef098d0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(length=15), nullable=False),
    sa.Column('verification_code', sa.String(length=6), nullable=True),
    sa.Column('verification_code_timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('phone_number')
    )
    op.create_table('special_date',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_phone_number', sa.String(), nullable=False),
    sa.Column('label', sa.String(length=50), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['user_phone_number'], ['user.phone_number'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('special_date')
    op.drop_table('user')
    # ### end Alembic commands ###
