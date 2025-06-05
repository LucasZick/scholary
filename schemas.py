# schemas.py
from decimal import Decimal
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date, time

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None # 'sub' (subject) é o ID do usuário (proprietário)

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    nome_completo: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    # role: Optional[str] = "operador" # Exemplo se tiver roles

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="A senha deve ter no mínimo 8 caracteres")

class User(UserBase): # Schema para resposta (o que a API retorna sobre o User)
    id_user: int
    model_config = ConfigDict(from_attributes=True)

class EscolaBase(BaseModel):
    nome_escola: str
    endereco_completo: str
    cnpj: Optional[str] = None
    telefone_escola: Optional[str] = None
    nome_contato_escola: Optional[str] = None
    email_contato_escola: Optional[EmailStr] = None

class EscolaCreate(EscolaBase):
    pass

class EscolaUpdate(BaseModel):
    nome_escola: Optional[str] = None
    endereco_completo: Optional[str] = None
    cnpj: Optional[str] = None
    telefone_escola: Optional[str] = None
    nome_contato_escola: Optional[str] = None
    email_contato_escola: Optional[EmailStr] = None

class Escola(EscolaBase):
    id_escola: int
    data_cadastro: datetime
    model_config = ConfigDict(from_attributes=True)

class ResponsavelBase(BaseModel):
    nome_completo: str
    cpf: str
    email: EmailStr
    telefone_principal: str
    telefone_secundario: Optional[str] = None
    endereco_completo: Optional[str] = None

class ResponsavelCreate(ResponsavelBase):
    pass

class ResponsavelUpdate(BaseModel):
    nome_completo: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone_principal: Optional[str] = None
    telefone_secundario: Optional[str] = None
    endereco_completo: Optional[str] = None

class Responsavel(ResponsavelBase):
    id_responsavel: int
    data_cadastro: datetime
    model_config = ConfigDict(from_attributes=True)

class AlunoBase(BaseModel):
    nome_completo_aluno: str
    data_nascimento: date
    id_responsavel_principal: int # ID de um Responsavel existente (do mesmo proprietário)
    id_responsavel_secundario: Optional[int] = None # ID de um Responsavel existente (do mesmo proprietário)
    id_escola: int # ID de uma Escola existente (do mesmo proprietário)
    endereco_embarque_predeterminado: str
    turma_serie: Optional[str] = None
    periodo_escolar: str
    observacoes_medicas: Optional[str] = None
    foto_aluno_url: Optional[str] = None
    status_aluno: Optional[str] = "Ativo"

class AlunoCreate(AlunoBase):
    pass

class AlunoUpdate(BaseModel):
    nome_completo_aluno: Optional[str] = None
    data_nascimento: Optional[date] = None
    id_responsavel_principal: Optional[int] = None
    id_responsavel_secundario: Optional[int] = None
    id_escola: Optional[int] = None
    endereco_embarque_predeterminado: Optional[str] = None
    turma_serie: Optional[str] = None
    periodo_escolar: Optional[str] = None
    observacoes_medicas: Optional[str] = None
    foto_aluno_url: Optional[str] = None
    status_aluno: Optional[str] = None

class Aluno(AlunoBase):
    id_aluno: int
    data_cadastro: datetime
    # Para exibir os objetos relacionados em vez de apenas IDs:
    # responsavel_principal_obj: Optional[Responsavel] = None # Renomeado para evitar conflito com id_responsavel_principal
    # escola_obj: Optional[Escola] = None # Renomeado para evitar conflito
    model_config = ConfigDict(from_attributes=True)

class MotoristaBase(BaseModel):
    nome_completo: str
    cpf: str # Validação de formato e unicidade por proprietário no backend
    cnh_numero: str # Validação de unicidade por proprietário no backend
    cnh_categoria: str
    cnh_validade: date
    telefone: str
    email: Optional[EmailStr] = None # Validação de unicidade por proprietário no backend
    ativo: Optional[bool] = True

class MotoristaCreate(MotoristaBase):
    pass

class MotoristaUpdate(BaseModel): # Para atualizações parciais
    nome_completo: Optional[str] = None
    # CPF e CNH geralmente não mudam, mas se permitir, adicione aqui
    cpf: Optional[str] = None 
    cnh_numero: Optional[str] = None
    cnh_categoria: Optional[str] = None
    cnh_validade: Optional[date] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None

class Motorista(MotoristaBase): # Schema de resposta
    id_motorista: int
    data_cadastro: datetime
    # id_proprietario_user: Optional[int] = None # Geralmente não precisa expor
    model_config = ConfigDict(from_attributes=True)

class VanBase(BaseModel):
    placa: str # Validação de formato e unicidade por proprietário no backend
    modelo_veiculo: str
    marca_veiculo: str
    ano_fabricacao: int
    capacidade_passageiros: int
    id_motorista_padrao: Optional[int] = None # ID de um Motorista existente (do mesmo proprietário)
    documentacao_em_dia: Optional[bool] = True
    seguro_validade: Optional[date] = None
    status_van: Optional[str] = "Ativa" # Ex: Ativa, Manutenção, Inativa

class VanCreate(VanBase):
    pass

class VanUpdate(BaseModel): # Para atualizações parciais
    placa: Optional[str] = None
    modelo_veiculo: Optional[str] = None
    marca_veiculo: Optional[str] = None
    ano_fabricacao: Optional[int] = None
    capacidade_passageiros: Optional[int] = None
    id_motorista_padrao: Optional[int] = None # Permitir alterar ou remover motorista padrão
    documentacao_em_dia: Optional[bool] = None
    seguro_validade: Optional[date] = None
    status_van: Optional[str] = None

class Van(VanBase): # Schema de resposta
    id_van: int
    data_cadastro: datetime
    # id_proprietario_user: Optional[int] = None # Geralmente não precisa expor
    # Se quiser retornar o objeto Motorista completo em vez do ID:
    # motorista_padrao_obj: Optional[Motorista] = None # Requereria que Motorista schema esteja definido antes
    model_config = ConfigDict(from_attributes=True)

class ContratoServicoBase(BaseModel):
    id_aluno: int # ID de um Aluno existente (do mesmo proprietário)
    id_responsavel_financeiro: int # ID de um Responsavel existente (do mesmo proprietário)
    data_inicio_contrato: date
    data_fim_contrato: Optional[date] = None
    valor_mensal: Decimal = Field(..., gt=Decimal('0.00'), description="Valor mensal do contrato, deve ser positivo.")
    dia_vencimento_mensalidade: int = Field(..., ge=1, le=31, description="Dia do mês para vencimento (1-31).")
    tipo_servico_contratado: str # Ex: "Transporte Integral", "Só Ida", "Só Volta"
    status_contrato: Optional[str] = "Ativo" # Ex: Ativo, Inativo, Cancelado, Concluído
    observacoes_contrato: Optional[str] = None

class ContratoServicoCreate(ContratoServicoBase):
    pass

class ContratoServicoUpdate(BaseModel): # Para atualizações parciais
    # Geralmente não se muda aluno ou responsável de um contrato, mas sim se cria um novo
    # ou se encerra o antigo. Mas se precisar, adicione os IDs aqui.
    # id_aluno: Optional[int] = None 
    # id_responsavel_financeiro: Optional[int] = None
    data_inicio_contrato: Optional[date] = None
    data_fim_contrato: Optional[date] = None # Permitir definir ou remover data de fim
    # VALIDAÇÃO ADICIONADA (se o campo for fornecido para atualização)
    valor_mensal: Optional[Decimal] = Field(default=None, gt=Decimal('0.00'), description="Novo valor mensal, deve ser positivo.")
    # VALIDAÇÃO ADICIONADA (se o campo for fornecido para atualização)
    dia_vencimento_mensalidade: Optional[int] = Field(default=None, ge=1, le=31, description="Novo dia de vencimento (1-31).")
    tipo_servico_contratado: Optional[str] = None
    status_contrato: Optional[str] = None
    observacoes_contrato: Optional[str] = None

class ContratoServico(ContratoServicoBase): # Schema de resposta
    id_contrato: int
    data_cadastro: datetime
    # id_proprietario_user: Optional[int] = None # Geralmente não precisa expor
    # Se quiser retornar os objetos Aluno e Responsavel completos:
    # aluno_obj: Optional[Aluno] = None # Renomear para evitar conflito com id_aluno
    # responsavel_financeiro_obj: Optional[Responsavel] = None # Renomear
    model_config = ConfigDict(from_attributes=True)

class PagamentoBase(BaseModel):
    id_contrato: int # ID de um ContratoServico existente (do mesmo proprietário)
    mes_referencia: str # Formato 'AAAA-MM'
    data_vencimento: date
    valor_nominal: Decimal
    valor_desconto: Optional[Decimal] = Decimal('0.00')
    valor_acrescimo: Optional[Decimal] = Decimal('0.00')
    valor_pago: Optional[Decimal] = None
    data_pagamento: Optional[date] = None
    metodo_pagamento: Optional[str] = None # Ex: Boleto, PIX, Cartão
    status_pagamento: Optional[str] = "Pendente" # Ex: Pendente, Pago, Atrasado, Cancelado
    id_transacao_gateway: Optional[str] = None
    link_boleto_comprovante: Optional[str] = None
    observacoes_pagamento: Optional[str] = None
    # data_baixa não é geralmente enviado na criação/atualização, mas sim por um processo interno

class PagamentoCreate(PagamentoBase):
    pass

class PagamentoUpdate(BaseModel): # Para atualizações parciais (ex: registrar um pagamento)
    # id_contrato e mes_referencia geralmente não mudam em um pagamento existente
    data_vencimento: Optional[date] = None
    valor_nominal: Optional[Decimal] = None # Menos comum alterar, mas possível
    valor_desconto: Optional[Decimal] = None
    valor_acrescimo: Optional[Decimal] = None
    valor_pago: Optional[Decimal] = None
    data_pagamento: Optional[date] = None
    metodo_pagamento: Optional[str] = None
    status_pagamento: Optional[str] = None
    id_transacao_gateway: Optional[str] = None
    link_boleto_comprovante: Optional[str] = None
    observacoes_pagamento: Optional[str] = None
    # data_baixa seria atualizada internamente

class Pagamento(PagamentoBase): # Schema de resposta
    id_pagamento: int
    data_geracao: datetime
    data_baixa: Optional[datetime] = None
    # id_proprietario_user não está diretamente no Pagamento, mas no Contrato.
    # Se quiser mostrar o objeto ContratoServico:
    # contrato_obj: Optional[ContratoServico] = None
    model_config = ConfigDict(from_attributes=True)

class RotaBase(BaseModel):
    nome_rota: str
    id_van_designada: int # ID de uma Van existente (do mesmo proprietário)
    id_motorista_escalado: int # ID de um Motorista existente (do mesmo proprietário)
    id_escola_atendida: int # ID de uma Escola existente (do mesmo proprietário)
    tipo_rota: str # Ex: "Ida Manhã", "Volta Tarde", "Completa Manhã"
    horario_partida_estimado: Optional[time] = None
    horario_chegada_estimado_escola: Optional[time] = None
    horario_retorno_estimado_escola: Optional[time] = None
    observacoes_rota: Optional[str] = None
    ativa: Optional[bool] = True

class RotaCreate(RotaBase):
    pass

class RotaUpdate(BaseModel): # Para atualizações parciais
    nome_rota: Optional[str] = None
    id_van_designada: Optional[int] = None
    id_motorista_escalado: Optional[int] = None
    id_escola_atendida: Optional[int] = None
    tipo_rota: Optional[str] = None
    horario_partida_estimado: Optional[time] = None
    horario_chegada_estimado_escola: Optional[time] = None
    horario_retorno_estimado_escola: Optional[time] = None
    observacoes_rota: Optional[str] = None
    ativa: Optional[bool] = None

# Schema para a associação Aluno-Rota (o que o cliente envia para adicionar um aluno)
class AlunoEmRotaCreate(BaseModel):
    id_aluno: int
    ordem_embarque_ida: Optional[int] = None
    ordem_desembarque_volta: Optional[int] = None
    ponto_embarque_especifico: Optional[str] = None
    ponto_desembarque_especifico: Optional[str] = None
    status_aluno_na_rota: Optional[str] = "Ativo"
    data_inicio_na_rota: Optional[date] = None # Se None, pode ser default para hoje no backend
    data_fim_na_rota: Optional[date] = None

# Schema para atualizar detalhes de um aluno em uma rota
class AlunoEmRotaUpdate(BaseModel):
    ordem_embarque_ida: Optional[int] = None
    ordem_desembarque_volta: Optional[int] = None
    ponto_embarque_especifico: Optional[str] = None
    ponto_desembarque_especifico: Optional[str] = None
    status_aluno_na_rota: Optional[str] = None # Ex: "Ativo", "Suspenso", "Inativo"
    data_fim_na_rota: Optional[date] = None # Para marcar como inativo

# Schema de resposta para AlunosPorRota, incluindo detalhes do Aluno
class AlunosPorRotaDetalhes(BaseModel):
    id_aluno_rota: int
    id_aluno: int # Ou o objeto Aluno completo
    id_rota: int  # Ou o objeto Rota completo (cuidado com recursão)
    aluno: Aluno # Exibindo o objeto Aluno completo
    ordem_embarque_ida: Optional[int] = None
    ordem_desembarque_volta: Optional[int] = None
    ponto_embarque_especifico: Optional[str] = None
    ponto_desembarque_especifico: Optional[str] = None
    status_aluno_na_rota: str
    data_inicio_na_rota: date
    data_fim_na_rota: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)


class Rota(RotaBase): # Schema de resposta para Rota
    id_rota: int
    data_cadastro: datetime
    # Para exibir os alunos diretamente na resposta da Rota:
    # alunos_na_rota: List[AlunosPorRotaDetalhes] = [] # Ou List[Aluno] se simplificar
    # Para exibir os objetos Van, Motorista, Escola em vez de IDs:
    # van_designada_obj: Optional[Van] = None
    # motorista_escalado_obj: Optional[Motorista] = None
    # escola_atendida_obj: Optional[Escola] = None
    model_config = ConfigDict(from_attributes=True)