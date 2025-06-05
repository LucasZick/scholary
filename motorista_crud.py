# motorista_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional

import app_models # Seu módulo de modelos SQLAlchemy
import schemas # Seu módulo de schemas Pydantic

def create_motorista(db: Session, motorista: schemas.MotoristaCreate, proprietario_id: int) -> app_models.Motorista:
    db_motorista = app_models.Motorista(
        **motorista.model_dump(),
        id_proprietario_user=proprietario_id
    )
    db.add(db_motorista)
    db.commit()
    db.refresh(db_motorista)
    return db_motorista

def get_motoristas_por_proprietario(db: Session, proprietario_id: int, skip: int = 0, limit: int = 100) -> List[app_models.Motorista]:
    return db.query(app_models.Motorista).filter(app_models.Motorista.id_proprietario_user == proprietario_id).offset(skip).limit(limit).all()

def get_motorista_por_id_e_proprietario(db: Session, motorista_id: int, proprietario_id: int) -> Optional[app_models.Motorista]:
    return db.query(app_models.Motorista).filter(
        app_models.Motorista.id_motorista == motorista_id,
        app_models.Motorista.id_proprietario_user == proprietario_id
    ).first()

def get_motorista_by_cpf_e_proprietario(db: Session, cpf: str, proprietario_id: int) -> Optional[app_models.Motorista]:
    return db.query(app_models.Motorista).filter(
        app_models.Motorista.cpf == cpf,
        app_models.Motorista.id_proprietario_user == proprietario_id
    ).first()

def get_motorista_by_cnh_e_proprietario(db: Session, cnh_numero: str, proprietario_id: int) -> Optional[app_models.Motorista]:
    return db.query(app_models.Motorista).filter(
        app_models.Motorista.cnh_numero == cnh_numero,
        app_models.Motorista.id_proprietario_user == proprietario_id
    ).first()

def get_motorista_by_email_e_proprietario(db: Session, email: str, proprietario_id: int) -> Optional[app_models.Motorista]:
    if not email: # Email pode ser opcional
        return None
    return db.query(app_models.Motorista).filter(
        app_models.Motorista.email == email,
        app_models.Motorista.id_proprietario_user == proprietario_id
    ).first()

def update_motorista(
    db: Session, motorista_id: int, motorista_update_data: schemas.MotoristaUpdate, proprietario_id: int
) -> Optional[app_models.Motorista]:
    db_motorista = get_motorista_por_id_e_proprietario(db, motorista_id=motorista_id, proprietario_id=proprietario_id)
    if not db_motorista:
        return None

    update_data = motorista_update_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_motorista, key, value)
    
    db.add(db_motorista)
    db.commit()
    db.refresh(db_motorista)
    return db_motorista

def delete_motorista(db: Session, motorista_id: int, proprietario_id: int) -> Optional[app_models.Motorista]:
    db_motorista = get_motorista_por_id_e_proprietario(db, motorista_id=motorista_id, proprietario_id=proprietario_id)
    if not db_motorista:
        return None
    
    # Adicionar lógica aqui para verificar se o motorista está associado a vans ou rotas ativas
    # antes de permitir a deleção, ou definir o motorista como inativo em vez de deletar.
    # Por enquanto, vamos permitir a deleção direta.
    
    db.delete(db_motorista)
    db.commit()
    return db_motorista