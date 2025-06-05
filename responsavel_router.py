# responsavel_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import responsavel_crud # NOVO
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/responsaveis",
    tags=["Responsaveis"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

@router.post("/", response_model=schemas.Responsavel, status_code=status.HTTP_201_CREATED)
def create_novo_responsavel(
    responsavel_in: schemas.ResponsavelCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Validação de CPF e Email duplicados para este proprietário
    db_responsavel_cpf = responsavel_crud.get_responsavel_by_cpf_e_proprietario(
        db, cpf=responsavel_in.cpf, proprietario_id=current_user.id_user
    )
    if db_responsavel_cpf:
        raise HTTPException(status_code=400, detail=f"Você já possui um responsável com o CPF '{responsavel_in.cpf}'.")
    
    db_responsavel_email = responsavel_crud.get_responsavel_by_email_e_proprietario(
        db, email=responsavel_in.email, proprietario_id=current_user.id_user
    )
    if db_responsavel_email:
        raise HTTPException(status_code=400, detail=f"Você já possui um responsável com o email '{responsavel_in.email}'.")
            
    return responsavel_crud.create_responsavel(db=db, responsavel=responsavel_in, proprietario_id=current_user.id_user)

@router.get("/", response_model=List[schemas.Responsavel])
def read_meus_responsaveis(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    responsaveis = responsavel_crud.get_responsaveis_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return responsaveis

@router.get("/{responsavel_id}", response_model=schemas.Responsavel)
def read_meu_responsavel_especifico(
    responsavel_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_responsavel = responsavel_crud.get_responsavel_por_id_e_proprietario(
        db, responsavel_id=responsavel_id, proprietario_id=current_user.id_user
    )
    if db_responsavel is None:
        raise HTTPException(status_code=404, detail="Responsável não encontrado ou não pertence a você")
    return db_responsavel

@router.put("/{responsavel_id}", response_model=schemas.Responsavel)
def update_meu_responsavel(
    responsavel_id: int,
    responsavel_update_data: schemas.ResponsavelUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    responsavel_original = responsavel_crud.get_responsavel_por_id_e_proprietario(db, responsavel_id=responsavel_id, proprietario_id=current_user.id_user)
    if not responsavel_original:
        raise HTTPException(status_code=404, detail="Responsável não encontrado ou não pertence a você para atualizar.")

    # Validações de CPF e Email duplicados (se alterados)
    if responsavel_update_data.cpf and responsavel_update_data.cpf != responsavel_original.cpf:
        outro_com_cpf = responsavel_crud.get_responsavel_by_cpf_e_proprietario(db, cpf=responsavel_update_data.cpf, proprietario_id=current_user.id_user)
        if outro_com_cpf and outro_com_cpf.id_responsavel != responsavel_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outro responsável com o CPF '{responsavel_update_data.cpf}'.")

    if responsavel_update_data.email and responsavel_update_data.email != responsavel_original.email:
        outro_com_email = responsavel_crud.get_responsavel_by_email_e_proprietario(db, email=responsavel_update_data.email, proprietario_id=current_user.id_user)
        if outro_com_email and outro_com_email.id_responsavel != responsavel_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outro responsável com o email '{responsavel_update_data.email}'.")
    
    updated_responsavel = responsavel_crud.update_responsavel(db, responsavel_id=responsavel_id, responsavel_update_data=responsavel_update_data, proprietario_id=current_user.id_user)
    if updated_responsavel is None:
        raise HTTPException(status_code=404, detail="Erro ao tentar atualizar o responsável.")
    return updated_responsavel

@router.delete("/{responsavel_id}", response_model=schemas.Responsavel)
def delete_meu_responsavel(
    responsavel_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_responsavel_deletado = responsavel_crud.delete_responsavel(db, responsavel_id=responsavel_id, proprietario_id=current_user.id_user)
    if db_responsavel_deletado is None:
        raise HTTPException(status_code=404, detail="Responsável não encontrado ou não pertence a você para deletar")
    return db_responsavel_deletado