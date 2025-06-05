# contrato_servico_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import contrato_servico_crud
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/contratos",
    tags=["Contratos de Servico"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

@router.post("/", response_model=schemas.ContratoServico, status_code=status.HTTP_201_CREATED)
def create_novo_contrato_servico(
    contrato_in: schemas.ContratoServicoCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    created_contrato = contrato_servico_crud.create_contrato_servico(
        db=db, contrato_in=contrato_in, proprietario_id=current_user.id_user
    )

    if isinstance(created_contrato, str): # Tratamento de erro do CRUD
        if created_contrato == "ERRO_ALUNO_INVALIDO":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno fornecido é inválido ou não pertence a você.")
        elif created_contrato == "ERRO_RESPONSAVEL_INVALIDO":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Responsável financeiro fornecido é inválido ou não pertence a você.")
        elif created_contrato == "ERRO_DATA_FIM_ANTERIOR_DATA_INICIO":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data final do contrato não pode ser anterior à data inicial.")
        elif created_contrato == "ERRO_INESPERADO_AO_SALVAR_CONTRATO_PAGAMENTOS":
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ocorreu um erro inesperado ao tentar salvar o contrato e seus pagamentos.")
        # Outros erros específicos podem ser adicionados aqui
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao criar contrato: {created_contrato}")
    
    # Não precisamos mais checar 'if not created_contrato' se o CRUD sempre retorna obj ou string de erro.
    return created_contrato

@router.get("/", response_model=List[schemas.ContratoServico])
def read_meus_contratos_servico(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    contratos = contrato_servico_crud.get_contratos_servico_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return contratos

@router.get("/{contrato_id}", response_model=schemas.ContratoServico)
def read_meu_contrato_servico_especifico(
    contrato_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_contrato = contrato_servico_crud.get_contrato_servico_por_id_e_proprietario(
        db, contrato_id=contrato_id, proprietario_id=current_user.id_user
    )
    if db_contrato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato de serviço não encontrado ou não pertence a você")
    return db_contrato

@router.put("/{contrato_id}", response_model=schemas.ContratoServico)
def update_meu_contrato_servico(
    contrato_id: int,
    contrato_update_data: schemas.ContratoServicoUpdate, # Schema de update
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # As validações de FKs (aluno, responsavel), se permitidas na atualização e alteradas,
    # são feitas dentro do CRUD agora.
    # A lógica de duplicidade de nome/cnpj para ESCOLAS (não contratos) estava no router de escolas.
    # Contratos geralmente não têm essas constraints de nome/identificador único além do ID.

    updated_contrato = contrato_servico_crud.update_contrato_servico(
        db, contrato_id=contrato_id, contrato_update_data=contrato_update_data, proprietario_id=current_user.id_user
    )

    if isinstance(updated_contrato, str): # Tratamento de erro do CRUD
        if updated_contrato == "ERRO_CONTRATO_NAO_ENCONTRADO":
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado ou não pertence a você para atualizar.")
        elif updated_contrato == "ERRO_ALUNO_INVALIDO_UPDATE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aluno fornecido para atualização é inválido ou não pertence a você.")
        elif updated_contrato == "ERRO_RESPONSAVEL_INVALIDO_UPDATE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Responsável financeiro fornecido para atualização é inválido ou não pertence a você.")
        elif updated_contrato == "ERRO_DATA_FIM_ANTERIOR_DATA_INICIO_UPDATE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A nova data final do contrato não pode ser anterior à data inicial.")
        elif updated_contrato == "ERRO_INESPERADO_AO_ATUALIZAR_CONTRATO_PAGAMENTOS": # Novo erro do CRUD
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro inesperado ao atualizar contrato e seus pagamentos.")
        # Outros erros específicos retornados pelo CRUD podem ser tratados aqui
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao atualizar contrato: {updated_contrato}")
    
    return updated_contrato

@router.delete("/{contrato_id}", response_model=schemas.ContratoServico)
def delete_meu_contrato_servico(
    contrato_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_contrato_deletado = contrato_servico_crud.delete_contrato_servico(
        db, contrato_id=contrato_id, proprietario_id=current_user.id_user
    )
    if db_contrato_deletado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato de serviço não encontrado ou não pertence a você para deletar")
    return db_contrato_deletado