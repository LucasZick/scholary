# rota_crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Union
from datetime import date

import app_models
import schemas
# Importar CRUDs necessários para validação
import van_crud
import motorista_crud
import escola_crud
import aluno_crud

# --- CRUD para Rota ---
def create_rota(db: Session, rota_in: schemas.RotaCreate, proprietario_id: int) -> Union[app_models.Rota, str]:
    # Validação: Van, Motorista e Escola pertencem ao proprietário?
    van = van_crud.get_van_por_id_e_proprietario(db, van_id=rota_in.id_van_designada, proprietario_id=proprietario_id)
    if not van: return "ERRO_VAN_INVALIDA"
    
    motorista = motorista_crud.get_motorista_por_id_e_proprietario(db, motorista_id=rota_in.id_motorista_escalado, proprietario_id=proprietario_id)
    if not motorista: return "ERRO_MOTORISTA_INVALIDO"
    if not motorista.ativo: return "ERRO_MOTORISTA_INATIVO"

    escola = escola_crud.get_escola_por_id_e_proprietario(db, escola_id=rota_in.id_escola_atendida, proprietario_id=proprietario_id)
    if not escola: return "ERRO_ESCOLA_INVALIDA"

    db_rota = app_models.Rota(**rota_in.model_dump(), id_proprietario_user=proprietario_id)
    db.add(db_rota)
    db.commit()
    db.refresh(db_rota)
    return db_rota

def get_rotas_por_proprietario(db: Session, proprietario_id: int, skip: int = 0, limit: int = 100) -> List[app_models.Rota]:
    return db.query(app_models.Rota).filter(app_models.Rota.id_proprietario_user == proprietario_id).offset(skip).limit(limit).all()

def get_rota_por_id_e_proprietario(db: Session, rota_id: int, proprietario_id: int) -> Optional[app_models.Rota]:
    return db.query(app_models.Rota).filter(
        app_models.Rota.id_rota == rota_id,
        app_models.Rota.id_proprietario_user == proprietario_id
    ).first()

def get_rota_by_nome_e_proprietario(db: Session, nome_rota: str, proprietario_id: int) -> Optional[app_models.Rota]:
    return db.query(app_models.Rota).filter(
        app_models.Rota.nome_rota == nome_rota,
        app_models.Rota.id_proprietario_user == proprietario_id
    ).first()


def update_rota(
    db: Session, rota_id: int, rota_update_data: schemas.RotaUpdate, proprietario_id: int
) -> Optional[Union[app_models.Rota, str]]:
    db_rota = get_rota_por_id_e_proprietario(db, rota_id=rota_id, proprietario_id=proprietario_id)
    if not db_rota:
        return None # Ou "ERRO_ROTA_NAO_ENCONTRADA"

    update_data = rota_update_data.model_dump(exclude_unset=True)

    # Validações se IDs de van, motorista ou escola forem alterados
    if "id_van_designada" in update_data and update_data["id_van_designada"] != db_rota.id_van_designada:
        van = van_crud.get_van_por_id_e_proprietario(db, van_id=update_data["id_van_designada"], proprietario_id=proprietario_id)
        if not van: return "ERRO_VAN_INVALIDA_UPDATE"
    
    if "id_motorista_escalado" in update_data and update_data["id_motorista_escalado"] != db_rota.id_motorista_escalado:
        motorista = motorista_crud.get_motorista_por_id_e_proprietario(db, motorista_id=update_data["id_motorista_escalado"], proprietario_id=proprietario_id)
        if not motorista: return "ERRO_MOTORISTA_INVALIDO_UPDATE"
        if not motorista.ativo : return "ERRO_MOTORISTA_INATIVO_UPDATE"


    if "id_escola_atendida" in update_data and update_data["id_escola_atendida"] != db_rota.id_escola_atendida:
        escola = escola_crud.get_escola_por_id_e_proprietario(db, escola_id=update_data["id_escola_atendida"], proprietario_id=proprietario_id)
        if not escola: return "ERRO_ESCOLA_INVALIDA_UPDATE"

    for key, value in update_data.items():
        setattr(db_rota, key, value)
    
    db.add(db_rota)
    db.commit()
    db.refresh(db_rota)
    return db_rota

def delete_rota(db: Session, rota_id: int, proprietario_id: int) -> Optional[app_models.Rota]:
    db_rota = get_rota_por_id_e_proprietario(db, rota_id=rota_id, proprietario_id=proprietario_id)
    if not db_rota:
        return None
    # A cascade delete no modelo Rota para alunos_na_rota cuidará das associações.
    db.delete(db_rota)
    db.commit()
    return db_rota

# --- CRUD para AlunosPorRota ---

def add_aluno_to_rota(
    db: Session, rota_id: int, aluno_rota_in: schemas.AlunoEmRotaCreate, proprietario_id: int
) -> Union[app_models.AlunosPorRota, str]:
    
    # 1. Verifica se a Rota pertence ao proprietário
    rota = get_rota_por_id_e_proprietario(db, rota_id=rota_id, proprietario_id=proprietario_id)
    if not rota:
        return "ERRO_ROTA_INVALIDA"

    # 2. Verifica se o Aluno pertence ao proprietário
    aluno = aluno_crud.get_aluno_por_id_e_proprietario(db, aluno_id=aluno_rota_in.id_aluno, proprietario_id=proprietario_id)
    if not aluno:
        return "ERRO_ALUNO_INVALIDO"
    
    # 3. Verifica se o aluno já está ativo nesta rota (sem data_fim_na_rota)
    # A UniqueConstraint no modelo AlunosPorRota ('id_aluno', 'id_rota', 'data_fim_na_rota')
    # permite múltiplas entradas se data_fim_na_rota for diferente (ou seja, uma entrada antiga inativada).
    # Precisamos verificar se já existe uma entrada ATIVA (data_fim_na_rota IS NULL) para este aluno nesta rota.
    
    associacao_ativa_existente = db.query(app_models.AlunosPorRota).filter(
        app_models.AlunosPorRota.id_aluno == aluno_rota_in.id_aluno,
        app_models.AlunosPorRota.id_rota == rota_id,
        app_models.AlunosPorRota.data_fim_na_rota == None # noqa (SQLAlchemy lida bem com None == NULL)
    ).first()

    if associacao_ativa_existente:
        return "ERRO_ALUNO_JA_ATIVO_NA_ROTA"

    data_inicio = aluno_rota_in.data_inicio_na_rota if aluno_rota_in.data_inicio_na_rota else date.today()

    db_aluno_rota = app_models.AlunosPorRota(
        id_aluno=aluno_rota_in.id_aluno,
        id_rota=rota_id,
        ordem_embarque_ida=aluno_rota_in.ordem_embarque_ida,
        ordem_desembarque_volta=aluno_rota_in.ordem_desembarque_volta,
        ponto_embarque_especifico=aluno_rota_in.ponto_embarque_especifico,
        ponto_desembarque_especifico=aluno_rota_in.ponto_desembarque_especifico,
        status_aluno_na_rota=aluno_rota_in.status_aluno_na_rota or "Ativo", # Default se não fornecido
        data_inicio_na_rota=data_inicio,
        data_fim_na_rota=aluno_rota_in.data_fim_na_rota
    )
    db.add(db_aluno_rota)
    try:
        db.commit()
        db.refresh(db_aluno_rota)
        return db_aluno_rota
    except IntegrityError: # Pode acontecer devido à UniqueConstraint
        db.rollback()
        return "ERRO_INTEGRIDADE_ALUNO_ROTA" # Aluno já na rota (considerando data_fim_na_rota)

def get_alunos_da_rota_detalhes(db: Session, rota_id: int, proprietario_id: int) -> Union[List[app_models.AlunosPorRota], str]:
    rota = get_rota_por_id_e_proprietario(db, rota_id=rota_id, proprietario_id=proprietario_id)
    if not rota:
        return "ERRO_ROTA_INVALIDA"
    # Retorna os objetos AlunosPorRota, que têm o relacionamento 'aluno' para pegar os detalhes do aluno.
    return db.query(app_models.AlunosPorRota).filter(app_models.AlunosPorRota.id_rota == rota_id).all()

def get_aluno_rota_associacao_por_id(db: Session, aluno_rota_id: int, proprietario_id: int) -> Optional[app_models.AlunosPorRota]:
    # Verifica a propriedade através da rota associada
    return db.query(app_models.AlunosPorRota).join(app_models.Rota).filter(
        app_models.AlunosPorRota.id_aluno_rota == aluno_rota_id,
        app_models.Rota.id_proprietario_user == proprietario_id
    ).first()


def update_aluno_na_rota(
    db: Session, aluno_rota_id: int, aluno_rota_update_data: schemas.AlunoEmRotaUpdate, proprietario_id: int
) -> Optional[Union[app_models.AlunosPorRota, str]]:
    db_aluno_rota = get_aluno_rota_associacao_por_id(db, aluno_rota_id=aluno_rota_id, proprietario_id=proprietario_id)
    if not db_aluno_rota:
        return None # Ou "ERRO_ASSOCIACAO_NAO_ENCONTRADA"
    
    update_data = aluno_rota_update_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_aluno_rota, key, value)
    
    db.add(db_aluno_rota)
    db.commit()
    db.refresh(db_aluno_rota)
    return db_aluno_rota

def remove_aluno_da_rota(db: Session, aluno_rota_id: int, proprietario_id: int) -> Optional[app_models.AlunosPorRota]:
    """ Em vez de deletar, marca a associação como inativa setando data_fim_na_rota.
        Se realmente quiser deletar o registro, use db.delete().
    """
    db_aluno_rota = get_aluno_rota_associacao_por_id(db, aluno_rota_id=aluno_rota_id, proprietario_id=proprietario_id)
    if not db_aluno_rota:
        return None
    
    db_aluno_rota.data_fim_na_rota = date.today()
    db_aluno_rota.status_aluno_na_rota = "Inativo" # Ou um status específico
    db.add(db_aluno_rota)
    db.commit()
    db.refresh(db_aluno_rota)
    return db_aluno_rota

# Função para efetivamente deletar a associação, se necessário
def delete_associacao_aluno_rota(db: Session, aluno_rota_id: int, proprietario_id: int) -> Optional[app_models.AlunosPorRota]:
    db_aluno_rota = get_aluno_rota_associacao_por_id(db, aluno_rota_id=aluno_rota_id, proprietario_id=proprietario_id)
    if not db_aluno_rota:
        return None
    db.delete(db_aluno_rota)
    db.commit()
    return db_aluno_rota