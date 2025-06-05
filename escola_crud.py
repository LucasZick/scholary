# escola_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional

import app_models
import schemas

def create_escola(db: Session, escola: schemas.EscolaCreate, proprietario_id: int) -> app_models.Escola:
    db_escola = app_models.Escola(
        **escola.model_dump(), # Pega todos os campos do schema EscolaCreate
        id_proprietario_user=proprietario_id
    )
    db.add(db_escola)
    db.commit()
    db.refresh(db_escola)
    return db_escola

def get_escolas_por_proprietario(db: Session, proprietario_id: int, skip: int = 0, limit: int = 100) -> List[app_models.Escola]:
    return db.query(app_models.Escola).filter(app_models.Escola.id_proprietario_user == proprietario_id).offset(skip).limit(limit).all()

def get_escola_por_id_e_proprietario(db: Session, escola_id: int, proprietario_id: int) -> Optional[app_models.Escola]:
    return db.query(app_models.Escola).filter(
        app_models.Escola.id_escola == escola_id,
        app_models.Escola.id_proprietario_user == proprietario_id
    ).first()

def get_escola_by_nome_e_proprietario(db: Session, nome_escola: str, proprietario_id: int) -> Optional[app_models.Escola]:
    return db.query(app_models.Escola).filter(
        app_models.Escola.nome_escola == nome_escola,
        app_models.Escola.id_proprietario_user == proprietario_id
    ).first()

def get_escola_by_cnpj_e_proprietario(db: Session, cnpj: str, proprietario_id: int) -> Optional[app_models.Escola]:
    if not cnpj: 
        return None
    return db.query(app_models.Escola).filter(
        app_models.Escola.cnpj == cnpj,
        app_models.Escola.id_proprietario_user == proprietario_id
    ).first()

def update_escola(
    db: Session, escola_id: int, escola_update_data: schemas.EscolaUpdate, proprietario_id: int
) -> Optional[app_models.Escola]:
    db_escola = get_escola_por_id_e_proprietario(db, escola_id=escola_id, proprietario_id=proprietario_id)
    if not db_escola:
        return None # Ou levantar uma exceção que o router trata

    update_data = escola_update_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_escola, key, value)
    
    db.add(db_escola)
    db.commit()
    db.refresh(db_escola)
    return db_escola

def delete_escola(db: Session, escola_id: int, proprietario_id: int) -> Optional[app_models.Escola]:
    db_escola = get_escola_por_id_e_proprietario(db, escola_id=escola_id, proprietario_id=proprietario_id)
    if not db_escola:
        return None # Ou levantar uma exceção
    db.delete(db_escola)
    db.commit()
    return db_escola