# user_crud.py
from typing import Optional
from sqlalchemy.orm import Session
import app_models # Importa o pacote app_models
from core_utils import get_password_hash
import schemas # Importa o arquivo schemas.py

def get_user_by_email(db: Session, email: str) -> Optional[app_models.User]:
    return db.query(app_models.User).filter(app_models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[app_models.User]:
    return db.query(app_models.User).filter(app_models.User.id_user == user_id).first()

def create_user(db: Session, user: schemas.UserCreate) -> app_models.User:
    hashed_password = get_password_hash(user.password)
    db_user = app_models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        nome_completo=user.nome_completo,
        is_active=user.is_active if user.is_active is not None else True,
        is_superuser=user.is_superuser if user.is_superuser is not None else False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user