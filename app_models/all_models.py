# app_models/all_models.py
from sqlalchemy import (
    create_engine, Column, Integer, String, Date, ForeignKey, Text,
    DateTime, Numeric, Boolean, Time, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id_user = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    nome_completo = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    # role = Column(String(50), default='operador') # Futuramente para diferenciar tipos de usuários logados
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos (o que este usuário "possui")
    escolas_proprias = relationship("Escola", back_populates="proprietario", cascade="all, delete-orphan")
    vans_proprias = relationship("Van", back_populates="proprietario", cascade="all, delete-orphan")
    motoristas_proprios = relationship("Motorista", back_populates="proprietario", cascade="all, delete-orphan")
    alunos_proprios = relationship("Aluno", back_populates="proprietario", cascade="all, delete-orphan")
    responsaveis_proprios = relationship("Responsavel", back_populates="proprietario", cascade="all, delete-orphan")
    rotas_proprias = relationship("Rota", back_populates="proprietario", cascade="all, delete-orphan")
    contratos_proprios = relationship("ContratoServico", back_populates="proprietario", cascade="all, delete-orphan")


class Responsavel(Base):
    __tablename__ = "responsaveis"
    id_responsavel = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário
    
    nome_completo = Column(String(255), nullable=False)
    cpf = Column(String(14), nullable=False, index=True) # Unique por proprietário
    rg = Column(String(20))
    email = Column(String(255), nullable=False, index=True) # Unique por proprietário
    telefone_principal = Column(String(20), nullable=False)
    telefone_secundario = Column(String(20))
    endereco_completo = Column(Text)
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="responsaveis_proprios")
    alunos_como_principal = relationship("Aluno", foreign_keys="[Aluno.id_responsavel_principal]", back_populates="responsavel_principal")
    alunos_como_secundario = relationship("Aluno", foreign_keys="[Aluno.id_responsavel_secundario]", back_populates="responsavel_secundario")
    contratos_financeiros = relationship("ContratoServico", back_populates="responsavel_financeiro")
    
    __table_args__ = (
        UniqueConstraint('id_proprietario_user', 'cpf', name='uq_proprietario_responsavel_cpf'),
        UniqueConstraint('id_proprietario_user', 'email', name='uq_proprietario_responsavel_email'),
    )


class Escola(Base):
    __tablename__ = "escolas"
    id_escola = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário

    nome_escola = Column(String(255), nullable=False)
    cnpj = Column(String(18))
    endereco_completo = Column(Text, nullable=False)
    telefone_escola = Column(String(20))
    nome_contato_escola = Column(String(255))
    email_contato_escola = Column(String(255))
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="escolas_proprias")
    alunos = relationship("Aluno", back_populates="escola")
    rotas_atendidas = relationship("Rota", back_populates="escola_atendida")
    
    __table_args__ = (
        UniqueConstraint('id_proprietario_user', 'nome_escola', name='uq_proprietario_nome_escola'),
        UniqueConstraint('id_proprietario_user', 'cnpj', name='uq_proprietario_cnpj_escola'),
    )


class Motorista(Base):
    __tablename__ = "motoristas"
    id_motorista = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário
    
    nome_completo = Column(String(255), nullable=False)
    cpf = Column(String(14), nullable=False, index=True) # Unique por proprietário
    cnh_numero = Column(String(20), nullable=False, index=True) # Unique por proprietário
    cnh_categoria = Column(String(5), nullable=False)
    cnh_validade = Column(Date, nullable=False)
    telefone = Column(String(20), nullable=False)
    email = Column(String(255), index=True) # Unique por proprietário
    ativo = Column(Boolean, nullable=False, default=True)
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="motoristas_proprios")
    vans_padrao = relationship("Van", back_populates="motorista_padrao") # Um motorista pode ser o padrão de várias vans
    rotas_escaladas = relationship("Rota", back_populates="motorista_escalado") # Um motorista pode estar escalado em várias rotas

    __table_args__ = (
        UniqueConstraint('id_proprietario_user', 'cpf', name='uq_proprietario_motorista_cpf'),
        UniqueConstraint('id_proprietario_user', 'cnh_numero', name='uq_proprietario_motorista_cnh'),
        UniqueConstraint('id_proprietario_user', 'email', name='uq_proprietario_motorista_email'),
    )

class Van(Base):
    __tablename__ = "vans"
    id_van = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário
    
    placa = Column(String(10), nullable=False, index=True) # Unique por proprietário
    modelo_veiculo = Column(String(100), nullable=False)
    marca_veiculo = Column(String(100), nullable=False)
    ano_fabricacao = Column(Integer, nullable=False)
    capacidade_passageiros = Column(Integer, nullable=False)
    id_motorista_padrao = Column(Integer, ForeignKey("motoristas.id_motorista")) # FK para Motorista do mesmo proprietário
    documentacao_em_dia = Column(Boolean, nullable=False, default=True)
    seguro_validade = Column(Date)
    status_van = Column(String(50), nullable=False, default='Ativa')
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="vans_proprias")
    motorista_padrao = relationship("Motorista", back_populates="vans_padrao")
    rotas_designadas = relationship("Rota", back_populates="van_designada")

    __table_args__ = (
        UniqueConstraint('id_proprietario_user', 'placa', name='uq_proprietario_van_placa'),
    )


class Aluno(Base):
    __tablename__ = "alunos"
    id_aluno = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário
    
    nome_completo_aluno = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    # Chaves estrangeiras para Responsavel e Escola devem ser do mesmo proprietário (garantido na lógica da app)
    id_responsavel_principal = Column(Integer, ForeignKey("responsaveis.id_responsavel"), nullable=False)
    id_responsavel_secundario = Column(Integer, ForeignKey("responsaveis.id_responsavel"))
    id_escola = Column(Integer, ForeignKey("escolas.id_escola"), nullable=False)
    
    endereco_embarque_predeterminado = Column(Text, nullable=False)
    turma_serie = Column(String(50))
    periodo_escolar = Column(String(50), nullable=False)
    observacoes_medicas = Column(Text)
    foto_aluno_url = Column(String(512))
    status_aluno = Column(String(50), nullable=False, default='Ativo')
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="alunos_proprios")
    responsavel_principal = relationship("Responsavel", foreign_keys=[id_responsavel_principal], back_populates="alunos_como_principal")
    responsavel_secundario = relationship("Responsavel", foreign_keys=[id_responsavel_secundario], back_populates="alunos_como_secundario")
    escola = relationship("Escola", back_populates="alunos")
    contratos = relationship("ContratoServico", back_populates="aluno", cascade="all, delete-orphan")
    associacoes_rota = relationship("AlunosPorRota", back_populates="aluno", cascade="all, delete-orphan")


class Rota(Base):
    __tablename__ = "rotas"
    id_rota = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário
    
    nome_rota = Column(String(255), nullable=False) # Unique por proprietário
    # Chaves estrangeiras para Van, Motorista, Escola devem ser do mesmo proprietário (garantido na lógica da app)
    id_van_designada = Column(Integer, ForeignKey("vans.id_van"), nullable=False)
    id_motorista_escalado = Column(Integer, ForeignKey("motoristas.id_motorista"), nullable=False)
    id_escola_atendida = Column(Integer, ForeignKey("escolas.id_escola"), nullable=False)
    
    tipo_rota = Column(String(50), nullable=False)
    horario_partida_estimado = Column(Time)
    horario_chegada_estimado_escola = Column(Time)
    horario_retorno_estimado_escola = Column(Time)
    observacoes_rota = Column(Text)
    ativa = Column(Boolean, nullable=False, default=True)
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="rotas_proprias")
    van_designada = relationship("Van", back_populates="rotas_designadas")
    motorista_escalado = relationship("Motorista", back_populates="rotas_escaladas")
    escola_atendida = relationship("Escola", back_populates="rotas_atendidas")
    alunos_na_rota = relationship("AlunosPorRota", back_populates="rota", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('id_proprietario_user', 'nome_rota', name='uq_proprietario_nome_rota'),
    )


class AlunosPorRota(Base):
    __tablename__ = "alunos_por_rota"
    id_aluno_rota = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # id_proprietario_user aqui é implícito, pois Aluno e Rota já são do mesmo proprietário.
    
    id_aluno = Column(Integer, ForeignKey("alunos.id_aluno"), nullable=False)
    id_rota = Column(Integer, ForeignKey("rotas.id_rota"), nullable=False)
    ordem_embarque_ida = Column(Integer)
    ordem_desembarque_volta = Column(Integer)
    ponto_embarque_especifico = Column(Text)
    ponto_desembarque_especifico = Column(Text)
    status_aluno_na_rota = Column(String(50), nullable=False, default='Ativo')
    data_inicio_na_rota = Column(Date, nullable=False, server_default=func.now())
    data_fim_na_rota = Column(Date)

    aluno = relationship("Aluno", back_populates="associacoes_rota")
    rota = relationship("Rota", back_populates="alunos_na_rota")
    
    __table_args__ = (UniqueConstraint('id_aluno', 'id_rota', 'data_fim_na_rota', name='uq_aluno_rota_periodo_unico'),) # Um aluno não pode estar na mesma rota ao mesmo tempo


class ContratoServico(Base):
    __tablename__ = "contratos_servico"
    id_contrato = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_proprietario_user = Column(Integer, ForeignKey("users.id_user"), nullable=False, index=True) # Proprietário do contrato
    
    id_aluno = Column(Integer, ForeignKey("alunos.id_aluno"), nullable=False) # Aluno do mesmo proprietário
    id_responsavel_financeiro = Column(Integer, ForeignKey("responsaveis.id_responsavel"), nullable=False) # Responsável do mesmo proprietário
    
    data_inicio_contrato = Column(Date, nullable=False)
    data_fim_contrato = Column(Date)
    valor_mensal = Column(Numeric(10,2), nullable=False)
    dia_vencimento_mensalidade = Column(Integer, nullable=False)
    tipo_servico_contratado = Column(String(100), nullable=False)
    status_contrato = Column(String(50), nullable=False, default='Ativo')
    observacoes_contrato = Column(Text)
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    proprietario = relationship("User", back_populates="contratos_proprios")
    aluno = relationship("Aluno", back_populates="contratos")
    responsavel_financeiro = relationship("Responsavel", back_populates="contratos_financeiros")
    pagamentos = relationship("Pagamento", back_populates="contrato", cascade="all, delete-orphan")


class Pagamento(Base):
    __tablename__ = "pagamentos"
    id_pagamento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # id_proprietario_user é implícito através do ContratoServico
    
    id_contrato = Column(Integer, ForeignKey("contratos_servico.id_contrato"), nullable=False)
    
    mes_referencia = Column(String(7), nullable=False) # Formato 'AAAA-MM'
    ano_referencia = Column(Integer, nullable=False)
    data_vencimento = Column(Date, nullable=False)
    valor_nominal = Column(Numeric(10,2), nullable=False)
    valor_desconto = Column(Numeric(10,2), default=0.00)
    valor_acrescimo = Column(Numeric(10,2), default=0.00)
    valor_pago = Column(Numeric(10,2))
    data_pagamento = Column(Date)
    metodo_pagamento = Column(String(50))
    status_pagamento = Column(String(50), nullable=False, default='Pendente')
    id_transacao_gateway = Column(String(255))
    link_boleto_comprovante = Column(String(512))
    observacoes_pagamento = Column(Text)
    data_geracao = Column(DateTime(timezone=True), server_default=func.now())
    data_baixa = Column(DateTime(timezone=True))

    contrato = relationship("ContratoServico", back_populates="pagamentos")