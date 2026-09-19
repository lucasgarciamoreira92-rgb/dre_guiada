"""m3_dre_engine_adjustments"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None
def upgrade():
    op.create_table('period_adjustments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=30), nullable=False),
    sa.Column('amount', sa.Numeric(14, 2).with_variant(sa.BigInteger(), "sqlite"), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('observation', sa.String(length=2000), nullable=False),
    sa.Column('dre_effect', sa.String(length=30), nullable=False),
    sa.Column('deduction_kind', sa.String(length=30), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("(type = 'PROFIT_TAX' AND status = 'CONFIRMED' AND dre_effect = 'PROFIT_TAX' AND deduction_kind IS NULL) OR (type = 'OTHER_ADJUSTMENT' AND status = 'PENDING' AND dre_effect = 'PENDING' AND deduction_kind IS NULL) OR (type = 'REVENUE_DEDUCTION' AND status = 'CONFIRMED' AND dre_effect = 'REVENUE_DEDUCTION' AND deduction_kind IS NOT NULL AND deduction_kind IN ('REVENUE_TAX','RETURN','DISCOUNT','OTHER_APPROVED'))", name='ck_adjustment_rule'),
    sa.CheckConstraint("type IN ('PROFIT_TAX','OTHER_ADJUSTMENT','REVENUE_DEDUCTION')", name='ck_adjustment_type'),
    sa.CheckConstraint('amount > 0 AND amount <= 99999999999999', name='ck_adjustment_amount'),
    sa.CheckConstraint('length(trim(observation)) > 0', name='ck_adjustment_observation'),
    sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('period_adjustments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_period_adjustments_period_id'), ['period_id'], unique=False)

    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.create_index('ix_transactions_company_competence', ['company_id', 'competence_year', 'competence_month'], unique=False)

def downgrade():
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_transactions_company_competence')

    with op.batch_alter_table('period_adjustments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_period_adjustments_period_id'))

    op.drop_table('period_adjustments')
