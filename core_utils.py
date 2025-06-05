# core_utils.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
import app_models
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Carregar .env
project_dir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(project_dir, '.env')
load_dotenv(dotenv_path)

# --- 1. Configurações ---
class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./missing_db.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_default_secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

settings = Settings()

# --- 2. Configuração do Banco de Dados para FastAPI ---
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. Segurança: Hashing de Senha ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- 4. Segurança: JWT (Tokens) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # O endpoint de login será /token

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# --- 5. Dependência para obter usuário atual ---
async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> app_models.User:
    
    import user_crud
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    subject_user_id = payload.get("sub")
    if subject_user_id is None:
        raise credentials_exception

    try:
        user_id = int(subject_user_id)
    except ValueError:
        # Se 'sub' não for um ID numérico, talvez você esteja usando email como 'sub'
        # Neste caso, a lógica aqui precisaria ser user_crud.get_user_by_email
        # Mas para o exemplo, vamos assumir que 'sub' é o user.id_user
        raise credentials_exception 

    user = user_crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: app_models.User = Depends(get_current_user)
) -> app_models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user