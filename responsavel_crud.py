# responsavel_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional

import app_models
import schemas

def create_responsavel(db: Session, responsavel: schemas.ResponsavelCreate, proprietario_id: int) -> app_models.Responsavel:
    db_responsavel = app_models.Responsavel(
        **responsavel.model_dump(),
        id_proprietario_user=proprietario_id
    )
    db.add(db_responsavel)
    db.commit()
    db.refresh(db_responsavel)
    return db_responsavel

def get_responsaveis_por_proprietario(db: Session, proprietario_id: int, skip: int = 0, limit: int = 100) -> List[app_models.Responsavel]:
    return db.query(app_models.Responsavel).filter(app_models.Responsavel.id_proprietario_user == proprietario_id).offset(skip).limit(limit).all()

def get_responsavel_por_id_e_proprietario(db: Session, responsavel_id: int, proprietario_id: int) -> Optional[app_models.Responsavel]:
    return db.query(app_models.Responsavel).filter(
        app_models.Responsavel.id_responsavel == responsavel_id,
        app_models.Responsavel.id_proprietario_user == proprietario_id
    ).first()

def get_responsavel_by_cpf_e_proprietario(db: Session, cpf: str, proprietario_id: int) -> Optional[app_models.Responsavel]:
    return db.query(app_models.Responsavel).filter(
        app_models.Responsavel.cpf == cpf,
        app_models.Responsavel.id_proprietario_user == proprietario_id
    ).first()

def get_responsavel_by_email_e_proprietario(db: Session, email: str, proprietario_id: int) -> Optional[app_models.Responsavel]:
    return db.query(app_models.Responsavel).filter(
        app_models.Responsavel.email == email,
        app_models.Responsavel.id_proprietario_user == proprietario_id
    ).first()

def update_responsavel(
    db: Session, responsavel_id: int, responsavel_update_data: schemas.ResponsavelUpdate, proprietario_id: int
) -> Optional[app_models.Responsavel]:
    db_responsavel = get_responsavel_por_id_e_proprietario(db, responsavel_id=responsavel_id, proprietario_id=proprietario_id)
    if not db_responsavel:
        return None

    update_data = responsavel_update_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_responsavel, key, value)
    
    db.add(db_responsavel)
    db.commit()
    db.refresh(db_responsavel)
    return db_responsavel

def delete_responsavel(db: Session, responsavel_id: int, proprietario_id: int) -> Optional[app_models.Responsavel]:
    db_responsavel = get_responsavel_por_id_e_proprietario(db, responsavel_id=responsavel_id, proprietario_id=proprietario_id)
    if not db_responsavel:
        return None
    db.delete(db_responsavel)
    db.commit()
    return db_responsavel