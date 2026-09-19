"""m2_transactions_subcategories"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

# Snapshot kept here so future application changes cannot alter this migration.
DEFAULTS = {'COST': ['Operação', 'Infraestrutura', 'Mercadorias/Produtos', 'Prestadores ligados à entrega', 'Outros custos'], 'EXPENSE': ['Pessoal', 'Administrativas', 'Comercial/Marketing', 'Tecnologia', 'Estrutura', 'Outras despesas'], 'INVESTMENT': ['Equipamentos', 'Veículos', 'Infraestrutura', 'Tecnologia/Software de longo prazo', 'Outros investimentos'], 'FINANCIAL_EXPENSE': ['Juros', 'Tarifas bancárias', 'Encargos financeiros', 'Outras despesas financeiras']}
def upgrade():
    op.create_table('subcategories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('main_category', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('normalized_name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('active', sa.Boolean(), server_default='1', nullable=False),
    sa.Column('is_default', sa.Boolean(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("main_category IN ('REVENUE_RECURRING','REVENUE_SERVICE','REVENUE_PRODUCT','REVENUE_OTHER_OPERATING','FINANCIAL_REVENUE','NON_DRE','UNDEFINED','COST','EXPENSE','INVESTMENT','FINANCIAL_EXPENSE','TAX')", name='ck_subcategory_category'),
    sa.CheckConstraint('length(trim(name)) > 0', name='ck_subcategory_name'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('company_id', 'main_category', 'normalized_name', name='uq_subcategory_name'),
    sa.UniqueConstraint('id', 'company_id', 'main_category', name='uq_subcategory_identity')
    )
    with op.batch_alter_table('subcategories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_subcategories_company_id'), ['company_id'], unique=False)

    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('direction', sa.String(length=3), nullable=False),
    sa.Column('transaction_date', sa.Date(), nullable=False),
    sa.Column('competence_month', sa.Integer(), nullable=False),
    sa.Column('competence_year', sa.Integer(), nullable=False),
    sa.Column('competence_status', sa.String(length=20), nullable=False),
    sa.Column('competence_source', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('original_description', sa.String(length=500), nullable=False),
    sa.Column('amount', sa.Numeric(14, 2).with_variant(sa.BigInteger(), "sqlite"), nullable=False),
    sa.Column('main_category', sa.String(length=40), nullable=False),
    sa.Column('subcategory_id', sa.Integer(), nullable=True),
    sa.Column('dre_effect', sa.String(length=30), nullable=False),
    sa.Column('classification_status', sa.String(length=20), nullable=False),
    sa.Column('include_in_dre', sa.Boolean(), nullable=False),
    sa.Column('observation', sa.String(length=2000), nullable=True),
    sa.Column('origin_type', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("(direction = 'IN' AND main_category IN ('REVENUE_RECURRING','REVENUE_SERVICE','REVENUE_PRODUCT','REVENUE_OTHER_OPERATING','FINANCIAL_REVENUE','NON_DRE','UNDEFINED')) OR (direction = 'OUT' AND main_category IN ('COST','EXPENSE','INVESTMENT','FINANCIAL_EXPENSE','TAX','NON_DRE','UNDEFINED'))", name='ck_transaction_category'),
    sa.CheckConstraint("classification_status IN ('PENDING','CONFIRMED')", name='ck_transaction_classification'),
    sa.CheckConstraint("direction IN ('IN','OUT')", name='ck_transaction_direction'),
    sa.CheckConstraint("dre_effect IN ('GROSS_REVENUE','COST','OPERATING_EXPENSE','FINANCIAL_REVENUE','FINANCIAL_EXPENSE','NO_EFFECT','PENDING')", name='ck_transaction_effect'),
    sa.CheckConstraint("origin_type = 'MANUAL' AND competence_source = 'USER' AND competence_status = 'CONFIRMED'", name='ck_transaction_manual'),
    sa.CheckConstraint('amount > 0 AND amount <= 99999999999999', name='ck_transaction_amount'),
    sa.CheckConstraint('competence_month BETWEEN 1 AND 12', name='ck_transaction_month'),
    sa.CheckConstraint('competence_year BETWEEN 1900 AND 2100', name='ck_transaction_year'),
    sa.CheckConstraint('length(trim(description)) > 0', name='ck_transaction_description'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['period_id', 'company_id'], ['periods.id', 'periods.company_id'], name='fk_transaction_period_company'),
    sa.ForeignKeyConstraint(['subcategory_id', 'company_id', 'main_category'], ['subcategories.id', 'subcategories.company_id', 'subcategories.main_category'], name='fk_transaction_subcategory'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_transactions_company_id'), ['company_id'], unique=False)
        batch_op.create_index('ix_transactions_period_direction', ['period_id', 'direction'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_subcategory_id'), ['subcategory_id'], unique=False)

    with op.batch_alter_table('periods', schema=None) as batch_op:
        batch_op.create_index('uq_period_id_company', ['id', 'company_id'], unique=True)

    connection = op.get_bind()
    for company_id in connection.execute(sa.text('SELECT id FROM companies')).scalars():
        for category, names in DEFAULTS.items():
            for name in names:
                connection.execute(sa.text(
                    "INSERT INTO subcategories (company_id, main_category, name, normalized_name, is_default, created_at, updated_at) "
                    "VALUES (:company, :category, :name, :normalized, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ), dict(company=company_id, category=category, name=name, normalized=name.casefold()))


def downgrade():
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_transactions_subcategory_id'))
        batch_op.drop_index('ix_transactions_period_direction')
        batch_op.drop_index(batch_op.f('ix_transactions_company_id'))

    op.drop_table('transactions')
    with op.batch_alter_table('subcategories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subcategories_company_id'))

    op.drop_table('subcategories')

    with op.batch_alter_table('periods', schema=None) as batch_op:
        batch_op.drop_index('uq_period_id_company')
