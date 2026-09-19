IN_EFFECTS = {
    'REVENUE_RECURRING': 'GROSS_REVENUE',
    'REVENUE_SERVICE': 'GROSS_REVENUE',
    'REVENUE_PRODUCT': 'GROSS_REVENUE',
    'REVENUE_OTHER_OPERATING': 'GROSS_REVENUE',
    'FINANCIAL_REVENUE': 'FINANCIAL_REVENUE',
    'NON_DRE': 'NO_EFFECT', 'UNDEFINED': 'PENDING',
}
OUT_EFFECTS = {
    'COST': 'COST', 'EXPENSE': 'OPERATING_EXPENSE',
    'INVESTMENT': 'NO_EFFECT', 'FINANCIAL_EXPENSE': 'FINANCIAL_EXPENSE',
    'TAX': 'PENDING', 'NON_DRE': 'NO_EFFECT', 'UNDEFINED': 'PENDING',
}
EFFECTS = {'IN': IN_EFFECTS, 'OUT': OUT_EFFECTS}
CATEGORIES = tuple(dict.fromkeys([*IN_EFFECTS, *OUT_EFFECTS]))
DEFAULT_SUBCATEGORIES = {
    'COST': ['Operação', 'Infraestrutura', 'Mercadorias/Produtos', 'Prestadores ligados à entrega', 'Outros custos'],
    'EXPENSE': ['Pessoal', 'Administrativas', 'Comercial/Marketing', 'Tecnologia', 'Estrutura', 'Outras despesas'],
    'INVESTMENT': ['Equipamentos', 'Veículos', 'Infraestrutura', 'Tecnologia/Software de longo prazo', 'Outros investimentos'],
    'FINANCIAL_EXPENSE': ['Juros', 'Tarifas bancárias', 'Encargos financeiros', 'Outras despesas financeiras'],
}
