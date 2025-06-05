# van_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import van_crud # NOVO
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/vans",
    tags=["Vans"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

@router.post("/", response_model=schemas.Van, status_code=status.HTTP_201_CREATED)
def create_nova_van(
    van_in: schemas.VanCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Validação de placa duplicada para este proprietário
    if van_crud.get_van_by_placa_e_proprietario(db, placa=van_in.placa, proprietario_id=current_user.id_user):
        raise HTTPException(status_code=400, detail=f"Você já possui uma van com a placa '{van_in.placa}'.")
    
    created_van = van_crud.create_van(db=db, van=van_in, proprietario_id=current_user.id_user)

    if isinstance(created_van, str): # Tratamento de erro do CRUD (ex: motorista inválido)
        if created_van == "ERRO_MOTORISTA_PADRAO_INVALIDO":
            raise HTTPException(status_code=400, detail="Motorista padrão fornecido é inválido ou não pertence a você.")
        # Adicione outros tratamentos de erro se o CRUD retornar mais strings de erro
        raise HTTPException(status_code=500, detail="Erro interno ao criar van.")
    
    if not created_van: # Caso genérico
        raise HTTPException(status_code=400, detail="Não foi possível criar a van.")
    return created_van


@router.get("/", response_model=List[schemas.Van])
def read_minhas_vans(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    vans = van_crud.get_vans_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return vans

@router.get("/{van_id}", response_model=schemas.Van)
def read_minha_van_especifica(
    van_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_van = van_crud.get_van_por_id_e_proprietario(
        db, van_id=van_id, proprietario_id=current_user.id_user
    )
    if db_van is None:
        raise HTTPException(status_code=404, detail="Van não encontrada ou não pertence a você")
    return db_van

@router.put("/{van_id}", response_model=schemas.Van)
def update_minha_van(
    van_id: int,
    van_update_data: schemas.VanUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    van_original = van_crud.get_van_por_id_e_proprietario(db, van_id=van_id, proprietario_id=current_user.id_user)
    if not van_original:
        raise HTTPException(status_code=404, detail="Van não encontrada ou não pertence a você para atualizar.")

    # Validação de placa duplicada (se estiver sendo alterada)
    if van_update_data.placa and van_update_data.placa != van_original.placa:
        outra_van_com_placa = van_crud.get_van_by_placa_e_proprietario(db, placa=van_update_data.placa, proprietario_id=current_user.id_user)
        if outra_van_com_placa and outra_van_com_placa.id_van != van_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outra van com a placa '{van_update_data.placa}'.")
    
    updated_van = van_crud.update_van(db, van_id=van_id, van_update_data=van_update_data, proprietario_id=current_user.id_user)

    if isinstance(updated_van, str): # Erro de validação do CRUD (ex: motorista inválido)
        if updated_van == "ERRO_MOTORISTA_PADRAO_INVALIDO_UPDATE":
            raise HTTPException(status_code=400, detail="Motorista padrão fornecido para atualização é inválido ou não pertence a você.")
        # Adicione outros tratamentos de erro
        raise HTTPException(status_code=400, detail="Erro ao atualizar van: " + updated_van)

    if updated_van is None: # Se o CRUD principal retornou None
        raise HTTPException(status_code=404, detail="Erro ao tentar atualizar a van.")
    return updated_van

@router.delete("/{van_id}", response_model=schemas.Van)
def delete_minha_van(
    van_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_van_deletada = van_crud.delete_van(db, van_id=van_id, proprietario_id=current_user.id_user)
    if db_van_deletada is None:
        raise HTTPException(status_code=404, detail="Van não encontrada ou não pertence a você para deletar")
    return db_van_deletada