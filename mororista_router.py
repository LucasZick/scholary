# motorista_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import motorista_crud # NOVO
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/motoristas",
    tags=["Motoristas"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

@router.post("/", response_model=schemas.Motorista, status_code=status.HTTP_201_CREATED)
def create_novo_motorista(
    motorista_in: schemas.MotoristaCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Validação de CPF, CNH e Email duplicados para este proprietário
    if motorista_crud.get_motorista_by_cpf_e_proprietario(db, cpf=motorista_in.cpf, proprietario_id=current_user.id_user):
        raise HTTPException(status_code=400, detail=f"Você já possui um motorista com o CPF '{motorista_in.cpf}'.")
    
    if motorista_crud.get_motorista_by_cnh_e_proprietario(db, cnh_numero=motorista_in.cnh_numero, proprietario_id=current_user.id_user):
        raise HTTPException(status_code=400, detail=f"Você já possui um motorista com a CNH '{motorista_in.cnh_numero}'.")

    if motorista_in.email and motorista_crud.get_motorista_by_email_e_proprietario(db, email=motorista_in.email, proprietario_id=current_user.id_user):
        raise HTTPException(status_code=400, detail=f"Você já possui um motorista com o email '{motorista_in.email}'.")
            
    return motorista_crud.create_motorista(db=db, motorista=motorista_in, proprietario_id=current_user.id_user)

@router.get("/", response_model=List[schemas.Motorista])
def read_meus_motoristas(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    motoristas = motorista_crud.get_motoristas_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return motoristas

@router.get("/{motorista_id}", response_model=schemas.Motorista)
def read_meu_motorista_especifico(
    motorista_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_motorista = motorista_crud.get_motorista_por_id_e_proprietario(
        db, motorista_id=motorista_id, proprietario_id=current_user.id_user
    )
    if db_motorista is None:
        raise HTTPException(status_code=404, detail="Motorista não encontrado ou não pertence a você")
    return db_motorista

@router.put("/{motorista_id}", response_model=schemas.Motorista)
def update_meu_motorista(
    motorista_id: int,
    motorista_update_data: schemas.MotoristaUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    motorista_original = motorista_crud.get_motorista_por_id_e_proprietario(db, motorista_id=motorista_id, proprietario_id=current_user.id_user)
    if not motorista_original:
        raise HTTPException(status_code=404, detail="Motorista não encontrado ou não pertence a você para atualizar.")

    # Validações de CNH e Email se estiverem sendo alterados e já existirem em outro motorista SEU
    if motorista_update_data.cnh_numero and motorista_update_data.cnh_numero != motorista_original.cnh_numero:
        outro_motorista_com_cnh = motorista_crud.get_motorista_by_cnh_e_proprietario(db, cnh_numero=motorista_update_data.cnh_numero, proprietario_id=current_user.id_user)
        if outro_motorista_com_cnh and outro_motorista_com_cnh.id_motorista != motorista_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outro motorista com a CNH '{motorista_update_data.cnh_numero}'.")

    if motorista_update_data.email and motorista_update_data.email != motorista_original.email:
        outro_motorista_com_email = motorista_crud.get_motorista_by_email_e_proprietario(db, email=motorista_update_data.email, proprietario_id=current_user.id_user)
        if outro_motorista_com_email and outro_motorista_com_email.id_motorista != motorista_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outro motorista com o email '{motorista_update_data.email}'.")
    
    updated_motorista = motorista_crud.update_motorista(db, motorista_id=motorista_id, motorista_update_data=motorista_update_data, proprietario_id=current_user.id_user)
    if updated_motorista is None: # Não deve acontecer se motorista_original foi encontrado
        raise HTTPException(status_code=404, detail="Erro ao tentar atualizar o motorista.")
    return updated_motorista

@router.delete("/{motorista_id}", response_model=schemas.Motorista)
def delete_meu_motorista(
    motorista_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Antes de deletar, você pode querer verificar se este motorista está associado a alguma Van ou Rota ativa.
    # Se estiver, talvez você não queira permitir a deleção ou queira forçar a desassociação primeiro.
    # Por enquanto, a deleção é direta.
    db_motorista_deletado = motorista_crud.delete_motorista(db, motorista_id=motorista_id, proprietario_id=current_user.id_user)
    if db_motorista_deletado is None:
        raise HTTPException(status_code=404, detail="Motorista não encontrado ou não pertence a você para deletar")
    return db_motorista_deletado