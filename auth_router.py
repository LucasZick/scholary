# auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import schemas # Importa o schemas.py
import user_crud # Importa o user_crud.py
import app_models # Importa o pacote app_models
from core_utils import get_db, verify_password, create_access_token, settings # Importa de core_utils.py

router = APIRouter(
    tags=["Autenticação"]
)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends() # username aqui é o email
):
    user = user_crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id_user)}, # 'sub' é o ID do usuário como string
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Endpoint de exemplo para criar um usuário (você pode querer mais segurança aqui)
@router.post("/users/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_new_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_email = user_crud.get_user_by_email(db, email=user_in.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email já registrado")
    # Adicione validação para username se estiver usando
    return user_crud.create_user(db=db, user=user_in)