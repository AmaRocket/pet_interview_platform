"""add relation grade to result grade

Revision ID: 7f42a69b6c8e
Revises: 17172edde53b
Create Date: 2021-12-29 20:08:43.516005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f42a69b6c8e'
down_revision = '17172edde53b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('grade', 'result_grade')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('grade', sa.Column('result_grade', sa.REAL(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
