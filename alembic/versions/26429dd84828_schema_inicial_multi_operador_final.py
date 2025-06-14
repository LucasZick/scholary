"""schema_inicial_multi_operador_final

Revision ID: 26429dd84828
Revises: 
Create Date: 2025-05-28 15:51:06.662206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26429dd84828'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id_user', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=True),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('nome_completo', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id_user')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id_user'), 'users', ['id_user'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('escolas',
    sa.Column('id_escola', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('nome_escola', sa.String(length=255), nullable=False),
    sa.Column('cnpj', sa.String(length=18), nullable=True),
    sa.Column('endereco_completo', sa.Text(), nullable=False),
    sa.Column('telefone_escola', sa.String(length=20), nullable=True),
    sa.Column('nome_contato_escola', sa.String(length=255), nullable=True),
    sa.Column('email_contato_escola', sa.String(length=255), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.PrimaryKeyConstraint('id_escola'),
    sa.UniqueConstraint('id_proprietario_user', 'cnpj', name='uq_proprietario_cnpj_escola'),
    sa.UniqueConstraint('id_proprietario_user', 'nome_escola', name='uq_proprietario_nome_escola')
    )
    op.create_index(op.f('ix_escolas_id_escola'), 'escolas', ['id_escola'], unique=False)
    op.create_index(op.f('ix_escolas_id_proprietario_user'), 'escolas', ['id_proprietario_user'], unique=False)
    op.create_table('motoristas',
    sa.Column('id_motorista', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('nome_completo', sa.String(length=255), nullable=False),
    sa.Column('cpf', sa.String(length=14), nullable=False),
    sa.Column('cnh_numero', sa.String(length=20), nullable=False),
    sa.Column('cnh_categoria', sa.String(length=5), nullable=False),
    sa.Column('cnh_validade', sa.Date(), nullable=False),
    sa.Column('telefone', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.PrimaryKeyConstraint('id_motorista'),
    sa.UniqueConstraint('id_proprietario_user', 'cnh_numero', name='uq_proprietario_motorista_cnh'),
    sa.UniqueConstraint('id_proprietario_user', 'cpf', name='uq_proprietario_motorista_cpf'),
    sa.UniqueConstraint('id_proprietario_user', 'email', name='uq_proprietario_motorista_email')
    )
    op.create_index(op.f('ix_motoristas_cnh_numero'), 'motoristas', ['cnh_numero'], unique=False)
    op.create_index(op.f('ix_motoristas_cpf'), 'motoristas', ['cpf'], unique=False)
    op.create_index(op.f('ix_motoristas_email'), 'motoristas', ['email'], unique=False)
    op.create_index(op.f('ix_motoristas_id_motorista'), 'motoristas', ['id_motorista'], unique=False)
    op.create_index(op.f('ix_motoristas_id_proprietario_user'), 'motoristas', ['id_proprietario_user'], unique=False)
    op.create_table('responsaveis',
    sa.Column('id_responsavel', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('nome_completo', sa.String(length=255), nullable=False),
    sa.Column('cpf', sa.String(length=14), nullable=False),
    sa.Column('rg', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('telefone_principal', sa.String(length=20), nullable=False),
    sa.Column('telefone_secundario', sa.String(length=20), nullable=True),
    sa.Column('endereco_completo', sa.Text(), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.PrimaryKeyConstraint('id_responsavel'),
    sa.UniqueConstraint('id_proprietario_user', 'cpf', name='uq_proprietario_responsavel_cpf'),
    sa.UniqueConstraint('id_proprietario_user', 'email', name='uq_proprietario_responsavel_email')
    )
    op.create_index(op.f('ix_responsaveis_cpf'), 'responsaveis', ['cpf'], unique=False)
    op.create_index(op.f('ix_responsaveis_email'), 'responsaveis', ['email'], unique=False)
    op.create_index(op.f('ix_responsaveis_id_proprietario_user'), 'responsaveis', ['id_proprietario_user'], unique=False)
    op.create_index(op.f('ix_responsaveis_id_responsavel'), 'responsaveis', ['id_responsavel'], unique=False)
    op.create_table('alunos',
    sa.Column('id_aluno', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('nome_completo_aluno', sa.String(length=255), nullable=False),
    sa.Column('data_nascimento', sa.Date(), nullable=False),
    sa.Column('id_responsavel_principal', sa.Integer(), nullable=False),
    sa.Column('id_responsavel_secundario', sa.Integer(), nullable=True),
    sa.Column('id_escola', sa.Integer(), nullable=False),
    sa.Column('endereco_embarque_predeterminado', sa.Text(), nullable=False),
    sa.Column('turma_serie', sa.String(length=50), nullable=True),
    sa.Column('periodo_escolar', sa.String(length=50), nullable=False),
    sa.Column('observacoes_medicas', sa.Text(), nullable=True),
    sa.Column('foto_aluno_url', sa.String(length=512), nullable=True),
    sa.Column('status_aluno', sa.String(length=50), nullable=False),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_escola'], ['escolas.id_escola'], ),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.ForeignKeyConstraint(['id_responsavel_principal'], ['responsaveis.id_responsavel'], ),
    sa.ForeignKeyConstraint(['id_responsavel_secundario'], ['responsaveis.id_responsavel'], ),
    sa.PrimaryKeyConstraint('id_aluno')
    )
    op.create_index(op.f('ix_alunos_id_aluno'), 'alunos', ['id_aluno'], unique=False)
    op.create_index(op.f('ix_alunos_id_proprietario_user'), 'alunos', ['id_proprietario_user'], unique=False)
    op.create_table('vans',
    sa.Column('id_van', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('placa', sa.String(length=10), nullable=False),
    sa.Column('modelo_veiculo', sa.String(length=100), nullable=False),
    sa.Column('marca_veiculo', sa.String(length=100), nullable=False),
    sa.Column('ano_fabricacao', sa.Integer(), nullable=False),
    sa.Column('capacidade_passageiros', sa.Integer(), nullable=False),
    sa.Column('id_motorista_padrao', sa.Integer(), nullable=True),
    sa.Column('documentacao_em_dia', sa.Boolean(), nullable=False),
    sa.Column('seguro_validade', sa.Date(), nullable=True),
    sa.Column('status_van', sa.String(length=50), nullable=False),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_motorista_padrao'], ['motoristas.id_motorista'], ),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.PrimaryKeyConstraint('id_van'),
    sa.UniqueConstraint('id_proprietario_user', 'placa', name='uq_proprietario_van_placa')
    )
    op.create_index(op.f('ix_vans_id_proprietario_user'), 'vans', ['id_proprietario_user'], unique=False)
    op.create_index(op.f('ix_vans_id_van'), 'vans', ['id_van'], unique=False)
    op.create_index(op.f('ix_vans_placa'), 'vans', ['placa'], unique=False)
    op.create_table('contratos_servico',
    sa.Column('id_contrato', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('id_aluno', sa.Integer(), nullable=False),
    sa.Column('id_responsavel_financeiro', sa.Integer(), nullable=False),
    sa.Column('data_inicio_contrato', sa.Date(), nullable=False),
    sa.Column('data_fim_contrato', sa.Date(), nullable=True),
    sa.Column('valor_mensal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('dia_vencimento_mensalidade', sa.Integer(), nullable=False),
    sa.Column('tipo_servico_contratado', sa.String(length=100), nullable=False),
    sa.Column('status_contrato', sa.String(length=50), nullable=False),
    sa.Column('observacoes_contrato', sa.Text(), nullable=True),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_aluno'], ['alunos.id_aluno'], ),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.ForeignKeyConstraint(['id_responsavel_financeiro'], ['responsaveis.id_responsavel'], ),
    sa.PrimaryKeyConstraint('id_contrato')
    )
    op.create_index(op.f('ix_contratos_servico_id_contrato'), 'contratos_servico', ['id_contrato'], unique=False)
    op.create_index(op.f('ix_contratos_servico_id_proprietario_user'), 'contratos_servico', ['id_proprietario_user'], unique=False)
    op.create_table('rotas',
    sa.Column('id_rota', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_proprietario_user', sa.Integer(), nullable=False),
    sa.Column('nome_rota', sa.String(length=255), nullable=False),
    sa.Column('id_van_designada', sa.Integer(), nullable=False),
    sa.Column('id_motorista_escalado', sa.Integer(), nullable=False),
    sa.Column('id_escola_atendida', sa.Integer(), nullable=False),
    sa.Column('tipo_rota', sa.String(length=50), nullable=False),
    sa.Column('horario_partida_estimado', sa.Time(), nullable=True),
    sa.Column('horario_chegada_estimado_escola', sa.Time(), nullable=True),
    sa.Column('horario_retorno_estimado_escola', sa.Time(), nullable=True),
    sa.Column('observacoes_rota', sa.Text(), nullable=True),
    sa.Column('ativa', sa.Boolean(), nullable=False),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['id_escola_atendida'], ['escolas.id_escola'], ),
    sa.ForeignKeyConstraint(['id_motorista_escalado'], ['motoristas.id_motorista'], ),
    sa.ForeignKeyConstraint(['id_proprietario_user'], ['users.id_user'], ),
    sa.ForeignKeyConstraint(['id_van_designada'], ['vans.id_van'], ),
    sa.PrimaryKeyConstraint('id_rota'),
    sa.UniqueConstraint('id_proprietario_user', 'nome_rota', name='uq_proprietario_nome_rota')
    )
    op.create_index(op.f('ix_rotas_id_proprietario_user'), 'rotas', ['id_proprietario_user'], unique=False)
    op.create_index(op.f('ix_rotas_id_rota'), 'rotas', ['id_rota'], unique=False)
    op.create_table('alunos_por_rota',
    sa.Column('id_aluno_rota', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_aluno', sa.Integer(), nullable=False),
    sa.Column('id_rota', sa.Integer(), nullable=False),
    sa.Column('ordem_embarque_ida', sa.Integer(), nullable=True),
    sa.Column('ordem_desembarque_volta', sa.Integer(), nullable=True),
    sa.Column('ponto_embarque_especifico', sa.Text(), nullable=True),
    sa.Column('ponto_desembarque_especifico', sa.Text(), nullable=True),
    sa.Column('status_aluno_na_rota', sa.String(length=50), nullable=False),
    sa.Column('data_inicio_na_rota', sa.Date(), server_default=sa.text('now()'), nullable=False),
    sa.Column('data_fim_na_rota', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['id_aluno'], ['alunos.id_aluno'], ),
    sa.ForeignKeyConstraint(['id_rota'], ['rotas.id_rota'], ),
    sa.PrimaryKeyConstraint('id_aluno_rota'),
    sa.UniqueConstraint('id_aluno', 'id_rota', 'data_fim_na_rota', name='uq_aluno_rota_periodo_unico')
    )
    op.create_index(op.f('ix_alunos_por_rota_id_aluno_rota'), 'alunos_por_rota', ['id_aluno_rota'], unique=False)
    op.create_table('pagamentos',
    sa.Column('id_pagamento', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_contrato', sa.Integer(), nullable=False),
    sa.Column('mes_referencia', sa.String(length=7), nullable=False),
    sa.Column('ano_referencia', sa.Integer(), nullable=False),
    sa.Column('data_vencimento', sa.Date(), nullable=False),
    sa.Column('valor_nominal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_desconto', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('valor_acrescimo', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('valor_pago', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('data_pagamento', sa.Date(), nullable=True),
    sa.Column('metodo_pagamento', sa.String(length=50), nullable=True),
    sa.Column('status_pagamento', sa.String(length=50), nullable=False),
    sa.Column('id_transacao_gateway', sa.String(length=255), nullable=True),
    sa.Column('link_boleto_comprovante', sa.String(length=512), nullable=True),
    sa.Column('observacoes_pagamento', sa.Text(), nullable=True),
    sa.Column('data_geracao', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('data_baixa', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['id_contrato'], ['contratos_servico.id_contrato'], ),
    sa.PrimaryKeyConstraint('id_pagamento')
    )
    op.create_index(op.f('ix_pagamentos_id_pagamento'), 'pagamentos', ['id_pagamento'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_pagamentos_id_pagamento'), table_name='pagamentos')
    op.drop_table('pagamentos')
    op.drop_index(op.f('ix_alunos_por_rota_id_aluno_rota'), table_name='alunos_por_rota')
    op.drop_table('alunos_por_rota')
    op.drop_index(op.f('ix_rotas_id_rota'), table_name='rotas')
    op.drop_index(op.f('ix_rotas_id_proprietario_user'), table_name='rotas')
    op.drop_table('rotas')
    op.drop_index(op.f('ix_contratos_servico_id_proprietario_user'), table_name='contratos_servico')
    op.drop_index(op.f('ix_contratos_servico_id_contrato'), table_name='contratos_servico')
    op.drop_table('contratos_servico')
    op.drop_index(op.f('ix_vans_placa'), table_name='vans')
    op.drop_index(op.f('ix_vans_id_van'), table_name='vans')
    op.drop_index(op.f('ix_vans_id_proprietario_user'), table_name='vans')
    op.drop_table('vans')
    op.drop_index(op.f('ix_alunos_id_proprietario_user'), table_name='alunos')
    op.drop_index(op.f('ix_alunos_id_aluno'), table_name='alunos')
    op.drop_table('alunos')
    op.drop_index(op.f('ix_responsaveis_id_responsavel'), table_name='responsaveis')
    op.drop_index(op.f('ix_responsaveis_id_proprietario_user'), table_name='responsaveis')
    op.drop_index(op.f('ix_responsaveis_email'), table_name='responsaveis')
    op.drop_index(op.f('ix_responsaveis_cpf'), table_name='responsaveis')
    op.drop_table('responsaveis')
    op.drop_index(op.f('ix_motoristas_id_proprietario_user'), table_name='motoristas')
    op.drop_index(op.f('ix_motoristas_id_motorista'), table_name='motoristas')
    op.drop_index(op.f('ix_motoristas_email'), table_name='motoristas')
    op.drop_index(op.f('ix_motoristas_cpf'), table_name='motoristas')
    op.drop_index(op.f('ix_motoristas_cnh_numero'), table_name='motoristas')
    op.drop_table('motoristas')
    op.drop_index(op.f('ix_escolas_id_proprietario_user'), table_name='escolas')
    op.drop_index(op.f('ix_escolas_id_escola'), table_name='escolas')
    op.drop_table('escolas')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id_user'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
