# aluno_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import aluno_crud
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/alunos",
    tags=["Alunos"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

@router.post("/", response_model=schemas.Aluno, status_code=status.HTTP_201_CREATED)
def create_novo_aluno(
    aluno_in: schemas.AlunoCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # A validação de que escola e responsável pertencem ao usuário está no CRUD.
    # Poderia adicionar validação de duplicidade de aluno aqui (ex: mesmo nome e data de nasc. para o mesmo proprietário)
    created_aluno = aluno_crud.create_aluno(db=db, aluno_in=aluno_in, proprietario_id=current_user.id_user)
    
    if isinstance(created_aluno, str): # Se o CRUD retornou uma string de erro
        if created_aluno == "ERRO_ESCOLA_INVALIDA":
            raise HTTPException(status_code=400, detail="Escola fornecida é inválida ou não pertence a você.")
        elif created_aluno == "ERRO_RESPONSAVEL_PRINCIPAL_INVALIDO":
            raise HTTPException(status_code=400, detail="Responsável principal fornecido é inválido ou não pertence a você.")
        elif created_aluno == "ERRO_RESPONSAVEL_SECUNDARIO_INVALIDO":
            raise HTTPException(status_code=400, detail="Responsável secundário fornecido é inválido ou não pertence a você.")
        else: # Outro erro não previsto no CRUD
            raise HTTPException(status_code=500, detail="Erro interno ao criar aluno.")
    
    if not created_aluno: # Se o CRUD retornou None
        raise HTTPException(status_code=400, detail="Não foi possível criar o aluno por um motivo não especificado.")
    return created_aluno

@router.get("/", response_model=List[schemas.Aluno])
def read_meus_alunos(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    alunos = aluno_crud.get_alunos_por_proprietario(db, proprietario_id=current_user.id_user, skip=skip, limit=limit)
    return alunos

@router.get("/{aluno_id}", response_model=schemas.Aluno)
def read_meu_aluno_especifico(
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    aluno = aluno_crud.get_aluno_por_id_e_proprietario(db, aluno_id=aluno_id, proprietario_id=current_user.id_user)
    if aluno is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado ou não pertence a você.")
    return aluno

@router.put("/{aluno_id}", response_model=schemas.Aluno)
def update_meu_aluno(
    aluno_id: int,
    aluno_update_data: schemas.AlunoUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Validações de ID de escola/responsável (se alterados) estão no CRUD
    updated_aluno = aluno_crud.update_aluno(db, aluno_id=aluno_id, aluno_update_data=aluno_update_data, proprietario_id=current_user.id_user)
    
    if isinstance(updated_aluno, str): # Erro de validação do CRUD
        if updated_aluno == "ERRO_ESCOLA_INVALIDA_UPDATE":
            raise HTTPException(status_code=400, detail="Escola fornecida para atualização é inválida ou não pertence a você.")
        # Adicione mais tratamentos de erro aqui
        raise HTTPException(status_code=400, detail="Erro ao atualizar aluno: " + updated_aluno)
    
    if updated_aluno is None: # Aluno não encontrado ou não pertence ao usuário
        raise HTTPException(status_code=404, detail="Aluno não encontrado ou não pertence a você para atualizar.")
    return updated_aluno

@router.delete("/{aluno_id}", response_model=schemas.Aluno)
def delete_meu_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_aluno_deletado = aluno_crud.delete_aluno(db, aluno_id=aluno_id, proprietario_id=current_user.id_user)
    if db_aluno_deletado is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado ou não pertence a você para deletar")
    return db_aluno_deletado