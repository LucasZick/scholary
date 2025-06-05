# main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

import auth_router
import contrato_servico_router
import escola_router
import mororista_router
import pagamento_router
import responsavel_router
import aluno_router
import app_models
import rota_router
import schemas
from core_utils import get_current_active_user
import task_router
import van_router

app = FastAPI(
    title="API Transporte Escolar Multi-Operador",
    version="0.3.0" 
)

origins = [
    "http://localhost", # Para desenvolvimento local do Flutter Web (porta padrão)
    "http://localhost:8080", # Se você rodar o Flutter Web em uma porta específica
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Lista de origens permitidas
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, PUT, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)

# Incluir os roteadores
app.include_router(auth_router.router)
app.include_router(escola_router.router)
app.include_router(responsavel_router.router)
app.include_router(aluno_router.router)
app.include_router(mororista_router.router)
app.include_router(van_router.router)
app.include_router(contrato_servico_router.router)
app.include_router(pagamento_router.router)
app.include_router(rota_router.router)

app.include_router(task_router.router)


@app.get("/")
async def root():
    return {"message": "Bem-vindo à API de Transporte Escolar!"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: app_models.User = Depends(get_current_active_user)):
    return current_user

@app.get("/items/protected") 
async def read_protected_items(current_user: app_models.User = Depends(get_current_active_user)):
    return {"message": f"Olá {current_user.email}! Você está acessando um item protegido.", "user_id": current_user.id_user}