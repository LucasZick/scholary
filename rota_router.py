# rota_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import rota_crud # NOVO
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/rotas",
    tags=["Rotas e Alocação de Alunos"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

# --- Endpoints para Rotas ---
@router.post("/", response_model=schemas.Rota, status_code=status.HTTP_201_CREATED)
def create_nova_rota(
    rota_in: schemas.RotaCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Validação de nome de rota duplicado para este proprietário
    if rota_crud.get_rota_by_nome_e_proprietario(db, nome_rota=rota_in.nome_rota, proprietario_id=current_user.id_user):
        raise HTTPException(status_code=400, detail=f"Você já possui uma rota com o nome '{rota_in.nome_rota}'.")

    created_rota = rota_crud.create_rota(db=db, rota_in=rota_in, proprietario_id=current_user.id_user)

    if isinstance(created_rota, str): # Erro de validação do CRUD
        if created_rota == "ERRO_VAN_INVALIDA":
            raise HTTPException(status_code=400, detail="Van fornecida é inválida ou não pertence a você.")
        elif created_rota == "ERRO_MOTORISTA_INVALIDO":
            raise HTTPException(status_code=400, detail="Motorista fornecido é inválido ou não pertence a você.")
        elif created_rota == "ERRO_MOTORISTA_INATIVO":
            raise HTTPException(status_code=400, detail="Motorista fornecido está inativo.")
        elif created_rota == "ERRO_ESCOLA_INVALIDA":
            raise HTTPException(status_code=400, detail="Escola fornecida é inválida ou não pertence a você.")
        raise HTTPException(status_code=500, detail="Erro interno ao criar rota.")
    
    if not created_rota:
        raise HTTPException(status_code=400, detail="Não foi possível criar a rota.")
    return created_rota

@router.get("/", response_model=List[schemas.Rota])
def read_minhas_rotas(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    rotas = rota_crud.get_rotas_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return rotas

@router.get("/{rota_id}", response_model=schemas.Rota)
def read_minha_rota_especifica(
    rota_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_rota = rota_crud.get_rota_por_id_e_proprietario(
        db, rota_id=rota_id, proprietario_id=current_user.id_user
    )
    if db_rota is None:
        raise HTTPException(status_code=404, detail="Rota não encontrada ou não pertence a você")
    return db_rota

@router.put("/{rota_id}", response_model=schemas.Rota)
def update_minha_rota(
    rota_id: int,
    rota_update_data: schemas.RotaUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    rota_original = rota_crud.get_rota_por_id_e_proprietario(db, rota_id=rota_id, proprietario_id=current_user.id_user)
    if not rota_original:
        raise HTTPException(status_code=404, detail="Rota não encontrada ou não pertence a você para atualizar.")

    if rota_update_data.nome_rota and rota_update_data.nome_rota != rota_original.nome_rota:
        outra_rota_com_nome = rota_crud.get_rota_by_nome_e_proprietario(db, nome_rota=rota_update_data.nome_rota, proprietario_id=current_user.id_user)
        if outra_rota_com_nome and outra_rota_com_nome.id_rota != rota_id:
             raise HTTPException(status_code=400, detail=f"Você já possui outra rota com o nome '{rota_update_data.nome_rota}'.")
    
    updated_rota = rota_crud.update_rota(
        db, rota_id=rota_id, rota_update_data=rota_update_data, proprietario_id=current_user.id_user
    )
    if isinstance(updated_rota, str): # Erro de validação do CRUD
        # Adicione tratamentos para os erros de update_rota (ERRO_VAN_INVALIDA_UPDATE, etc.)
        raise HTTPException(status_code=400, detail="Erro ao atualizar rota: " + updated_rota)
    if updated_rota is None:
        raise HTTPException(status_code=404, detail="Erro ao tentar atualizar a rota.")
    return updated_rota

@router.delete("/{rota_id}", response_model=schemas.Rota)
def delete_minha_rota(
    rota_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_rota_deletada = rota_crud.delete_rota(db, rota_id=rota_id, proprietario_id=current_user.id_user)
    if db_rota_deletada is None:
        raise HTTPException(status_code=404, detail="Rota não encontrada ou não pertence a você para deletar")
    return db_rota_deletada


# --- Endpoints para Alunos em Rota ---

@router.post("/{rota_id}/alunos", response_model=schemas.AlunosPorRotaDetalhes, status_code=status.HTTP_201_CREATED)
def add_aluno_a_rota(
    rota_id: int,
    aluno_rota_in: schemas.AlunoEmRotaCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    associacao = rota_crud.add_aluno_to_rota(
        db, rota_id=rota_id, aluno_rota_in=aluno_rota_in, proprietario_id=current_user.id_user
    )
    if isinstance(associacao, str):
        if associacao == "ERRO_ROTA_INVALIDA":
            raise HTTPException(status_code=404, detail="Rota não encontrada ou não pertence a você.")
        elif associacao == "ERRO_ALUNO_INVALIDO":
            raise HTTPException(status_code=400, detail="Aluno fornecido é inválido ou não pertence a você.")
        elif associacao == "ERRO_ALUNO_JA_ATIVO_NA_ROTA":
            raise HTTPException(status_code=400, detail="Este aluno já está ativo nesta rota.")
        elif associacao == "ERRO_INTEGRIDADE_ALUNO_ROTA":
             raise HTTPException(status_code=400, detail="Não foi possível adicionar o aluno à rota devido a uma restrição de dados (possivelmente duplicidade com data_fim diferente).")
        raise HTTPException(status_code=500, detail="Erro ao adicionar aluno à rota.")
    
    if not associacao :
        raise HTTPException(status_code=400, detail="Não foi possível adicionar aluno à rota.")

    # Para retornar AlunosPorRotaDetalhes, precisamos carregar o aluno
    # O objeto associacao já é AlunosPorRota, que tem o relacionamento 'aluno'
    return associacao


@router.get("/{rota_id}/alunos", response_model=List[schemas.AlunosPorRotaDetalhes])
def get_alunos_em_rota(
    rota_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    alunos_associados = rota_crud.get_alunos_da_rota_detalhes(
        db, rota_id=rota_id, proprietario_id=current_user.id_user
    )
    if isinstance(alunos_associados, str): # Caso o CRUD retorne erro de rota inválida
        raise HTTPException(status_code=404, detail="Rota não encontrada ou não pertence a você.")
    return alunos_associados


# O ID aqui é o id_aluno_rota (da tabela de associação)
@router.put("/alunos-associados/{aluno_rota_id}", response_model=schemas.AlunosPorRotaDetalhes)
def update_detalhes_aluno_em_rota(
    aluno_rota_id: int,
    aluno_rota_update_data: schemas.AlunoEmRotaUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    updated_associacao = rota_crud.update_aluno_na_rota(
        db, aluno_rota_id=aluno_rota_id, aluno_rota_update_data=aluno_rota_update_data, proprietario_id=current_user.id_user
    )
    if isinstance(updated_associacao, str) or updated_associacao is None:
        raise HTTPException(status_code=404, detail="Associação aluno-rota não encontrada ou não pertence a você para atualizar.")
    return updated_associacao


# O ID aqui é o id_aluno_rota (da tabela de associação)
@router.patch("/alunos-associados/{aluno_rota_id}/desativar", response_model=schemas.AlunosPorRotaDetalhes)
def desativar_aluno_da_rota( # Nome mais específico para a ação
    aluno_rota_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Esta função no CRUD marca como inativo setando data_fim_na_rota
    associacao_desativada = rota_crud.remove_aluno_da_rota(
        db, aluno_rota_id=aluno_rota_id, proprietario_id=current_user.id_user
    )
    if associacao_desativada is None:
        raise HTTPException(status_code=404, detail="Associação aluno-rota não encontrada ou não pertence a você para desativar.")
    return associacao_desativada

# Se precisar de um endpoint para deletar permanentemente a associação:
# @router.delete("/alunos-associados/{aluno_rota_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_associacao_aluno_da_rota_permanente(
#     aluno_rota_id: int,
#     db: Session = Depends(get_db),
#     current_user: app_models.User = Depends(get_current_active_user)
# ):
#     deleted_associacao = rota_crud.delete_associacao_aluno_rota(
#         db, aluno_rota_id=aluno_rota_id, proprietario_id=current_user.id_user
#     )
#     if deleted_associacao is None:
#         raise HTTPException(status_code=404, detail="Associação aluno-rota não encontrada ou não pertence a você para deletar.")
#     return Response(status_code=status.HTTP_204_NO_CONTENT)