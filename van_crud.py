# van_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional, Union

import app_models # Seu módulo de modelos SQLAlchemy
import schemas # Seu módulo de schemas Pydantic
import motorista_crud # Para validar o id_motorista_padrao

def create_van(db: Session, van: schemas.VanCreate, proprietario_id: int) -> Union[app_models.Van, str]:
    # Validação: Se id_motorista_padrao foi fornecido, verificar se ele pertence ao proprietário
    if van.id_motorista_padrao is not None:
        motorista_existente = motorista_crud.get_motorista_por_id_e_proprietario(
            db, motorista_id=van.id_motorista_padrao, proprietario_id=proprietario_id
        )
        if not motorista_existente:
            return "ERRO_MOTORISTA_PADRAO_INVALIDO"

    db_van = app_models.Van(
        **van.model_dump(),
        id_proprietario_user=proprietario_id
    )
    db.add(db_van)
    db.commit()
    db.refresh(db_van)
    return db_van

def get_vans_por_proprietario(db: Session, proprietario_id: int, skip: int = 0, limit: int = 100) -> List[app_models.Van]:
    return db.query(app_models.Van).filter(app_models.Van.id_proprietario_user == proprietario_id).offset(skip).limit(limit).all()

def get_van_por_id_e_proprietario(db: Session, van_id: int, proprietario_id: int) -> Optional[app_models.Van]:
    return db.query(app_models.Van).filter(
        app_models.Van.id_van == van_id,
        app_models.Van.id_proprietario_user == proprietario_id
    ).first()

def get_van_by_placa_e_proprietario(db: Session, placa: str, proprietario_id: int) -> Optional[app_models.Van]:
    return db.query(app_models.Van).filter(
        app_models.Van.placa == placa,
        app_models.Van.id_proprietario_user == proprietario_id
    ).first()

def update_van(
    db: Session, van_id: int, van_update_data: schemas.VanUpdate, proprietario_id: int
) -> Optional[Union[app_models.Van, str]]:
    db_van = get_van_por_id_e_proprietario(db, van_id=van_id, proprietario_id=proprietario_id)
    if not db_van:
        return None # Ou "ERRO_VAN_NAO_ENCONTRADA"

    update_data = van_update_data.model_dump(exclude_unset=True)

    # Validação: Se id_motorista_padrao está sendo alterado
    if "id_motorista_padrao" in update_data:
        if update_data["id_motorista_padrao"] is not None: # Se está tentando definir um novo motorista
            motorista_existente = motorista_crud.get_motorista_por_id_e_proprietario(
                db, motorista_id=update_data["id_motorista_padrao"], proprietario_id=proprietario_id
            )
            if not motorista_existente:
                return "ERRO_MOTORISTA_PADRAO_INVALIDO_UPDATE"
        # Se update_data["id_motorista_padrao"] for None, está removendo o motorista padrão, o que é ok.
    
    for key, value in update_data.items():
        setattr(db_van, key, value)
    
    db.add(db_van)
    db.commit()
    db.refresh(db_van)
    return db_van

def delete_van(db: Session, van_id: int, proprietario_id: int) -> Optional[app_models.Van]:
    db_van = get_van_por_id_e_proprietario(db, van_id=van_id, proprietario_id=proprietario_id)
    if not db_van:
        return None
    
    # Adicionar lógica aqui para verificar se a van está associada a rotas ativas
    # antes de permitir a deleção, ou definir a van como inativa.
    # Por enquanto, deleção direta.
    
    db.delete(db_van)
    db.commit()
    return db_van