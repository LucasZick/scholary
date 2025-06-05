# escola_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import escola_crud
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/escolas",
    tags=["Escolas"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

@router.post("/", response_model=schemas.Escola, status_code=status.HTTP_201_CREATED)
def create_nova_escola_para_usuario_logado( # Nome da função mais descritivo
    escola_in: schemas.EscolaCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_escola_existente_nome = escola_crud.get_escola_by_nome_e_proprietario(
        db, nome_escola=escola_in.nome_escola, proprietario_id=current_user.id_user
    )
    if db_escola_existente_nome:
        raise HTTPException(status_code=400, detail=f"Você já possui uma escola com o nome '{escola_in.nome_escola}'.")
    
    if escola_in.cnpj:
        db_escola_existente_cnpj = escola_crud.get_escola_by_cnpj_e_proprietario(
            db, cnpj=escola_in.cnpj, proprietario_id=current_user.id_user
        )
        if db_escola_existente_cnpj:
            raise HTTPException(status_code=400, detail=f"Você já possui uma escola com o CNPJ '{escola_in.cnpj}'.")
            
    return escola_crud.create_escola(db=db, escola=escola_in, proprietario_id=current_user.id_user)

@router.get("/", response_model=List[schemas.Escola])
def read_minhas_escolas(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    escolas = escola_crud.get_escolas_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return escolas

@router.get("/{escola_id}", response_model=schemas.Escola)
def read_minha_escola_especifica( # Nome da função mais descritivo
    escola_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_escola = escola_crud.get_escola_por_id_e_proprietario(
        db, escola_id=escola_id, proprietario_id=current_user.id_user
    )
    if db_escola is None:
        raise HTTPException(status_code=404, detail="Escola não encontrada ou não pertence a você")
    return db_escola

@router.put("/{escola_id}", response_model=schemas.Escola)
def update_minha_escola( # Nome da função mais descritivo
    escola_id: int,
    escola_update_data: schemas.EscolaUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    escola_original = escola_crud.get_escola_por_id_e_proprietario(db, escola_id=escola_id, proprietario_id=current_user.id_user)
    if not escola_original:
        raise HTTPException(status_code=404, detail="Escola não encontrada ou não pertence a você para atualizar.")

    if escola_update_data.nome_escola and escola_update_data.nome_escola != escola_original.nome_escola:
        outra_escola_com_nome = escola_crud.get_escola_by_nome_e_proprietario(db, nome_escola=escola_update_data.nome_escola, proprietario_id=current_user.id_user)
        if outra_escola_com_nome and outra_escola_com_nome.id_escola != escola_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outra escola com o nome '{escola_update_data.nome_escola}'.")

    if escola_update_data.cnpj and escola_update_data.cnpj != escola_original.cnpj: # Adicionado 'and escola_update_data.cnpj' para evitar erro se for None
        outra_escola_com_cnpj = escola_crud.get_escola_by_cnpj_e_proprietario(db, cnpj=escola_update_data.cnpj, proprietario_id=current_user.id_user)
        if outra_escola_com_cnpj and outra_escola_com_cnpj.id_escola != escola_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outra escola com o CNPJ '{escola_update_data.cnpj}'.")

    updated_escola = escola_crud.update_escola(db, escola_id=escola_id, escola_update_data=escola_update_data, proprietario_id=current_user.id_user)
    # A função crud update_escola já garante que só atualiza se pertence ao proprietário pelo get_escola_por_id_e_proprietario
    # se db_escola for None lá, ele retorna None, então o router precisa tratar isso.
    # Mas como já verificamos com escola_original, essa checagem dupla não é estritamente necessária se o crud já faz.
    # No entanto, a lógica de verificar nome/cnpj duplicado ANTES de chamar o update é boa.
    if updated_escola is None: # Isso não deveria acontecer se escola_original foi encontrado
        raise HTTPException(status_code=404, detail="Erro ao tentar atualizar a escola.")
    return updated_escola

@router.delete("/{escola_id}", response_model=schemas.Escola)
def delete_minha_escola( # Nome da função mais descritivo
    escola_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_escola_deletada = escola_crud.delete_escola(db, escola_id=escola_id, proprietario_id=current_user.id_user)
    if db_escola_deletada is None:
        raise HTTPException(status_code=404, detail="Escola não encontrada ou não pertence a você para deletar")
    return db_escola_deletada