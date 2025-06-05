# pagamento_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas
import pagamento_crud # NOVO
import app_models
from core_utils import get_db, get_current_active_user

router = APIRouter(
    prefix="/pagamentos", # Rotas de pagamento diretas
    tags=["Pagamentos"],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Não autorizado"},
        404: {"description": "Não encontrado"}
    },
)

# Rota alternativa para listar pagamentos de um contrato específico:
# Poderia ser: /contratos/{contrato_id}/pagamentos
# Mas para simplificar, vamos listar todos os pagamentos do usuário e o cliente filtra,
# ou adicionamos um endpoint específico com filtro.

@router.post("/", response_model=schemas.Pagamento, status_code=status.HTTP_201_CREATED)
def create_novo_pagamento(
    pagamento_in: schemas.PagamentoCreate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    # Validação do contrato (se pertence ao usuário) está no CRUD.
    # Poderia adicionar validação para não permitir pagamentos duplicados para o mesmo contrato/mês-referência.
    
    created_pagamento = pagamento_crud.create_pagamento(
        db=db, pagamento_in=pagamento_in, proprietario_id=current_user.id_user
    )

    if isinstance(created_pagamento, str): # Tratamento de erro do CRUD
        if created_pagamento == "ERRO_CONTRATO_INVALIDO":
            raise HTTPException(status_code=400, detail="Contrato fornecido é inválido ou não pertence a você.")
        elif created_pagamento == "ERRO_MES_REFERENCIA_FORMATO":
            raise HTTPException(status_code=400, detail="Formato do mês de referência inválido. Use 'AAAA-MM'.")
        raise HTTPException(status_code=500, detail="Erro interno ao criar pagamento.")
    
    if not created_pagamento: # Genérico
        raise HTTPException(status_code=400, detail="Não foi possível criar o pagamento.")
    return created_pagamento

@router.get("/atrasados", response_model=List[schemas.Pagamento])
def read_meus_pagamentos_atrasados(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    """
    Retorna uma lista de todos os pagamentos atrasados
    (status 'Pendente' com data de vencimento passada OU status 'Atrasado')
    pertencentes ao operador logado.
    """
    pagamentos_atrasados = pagamento_crud.get_pagamentos_atrasados_por_proprietario(
        db, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    return pagamentos_atrasados

# Endpoint para listar pagamentos de um contrato específico do usuário logado
@router.get("/por-contrato/{contrato_id}", response_model=List[schemas.Pagamento])
def read_pagamentos_de_um_contrato(
    contrato_id: int,
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    pagamentos_ou_erro = pagamento_crud.get_pagamentos_por_contrato_e_proprietario(
        db, contrato_id=contrato_id, proprietario_id=current_user.id_user, skip=skip, limit=limit
    )
    if isinstance(pagamentos_ou_erro, str): # Se o CRUD retornou erro (contrato inválido)
        if pagamentos_ou_erro == "ERRO_CONTRATO_INVALIDO":
             raise HTTPException(status_code=404, detail="Contrato não encontrado ou não pertence a você.")
    
    return pagamentos_ou_erro # Retorna a lista de pagamentos

@router.get("/{pagamento_id}", response_model=schemas.Pagamento)
def read_meu_pagamento_especifico(
    pagamento_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_pagamento = pagamento_crud.get_pagamento_por_id_e_proprietario(
        db, pagamento_id=pagamento_id, proprietario_id=current_user.id_user
    )
    if db_pagamento is None:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado ou não pertence a você")
    return db_pagamento

@router.put("/{pagamento_id}", response_model=schemas.Pagamento)
def update_meu_pagamento(
    pagamento_id: int,
    pagamento_update_data: schemas.PagamentoUpdate,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    updated_pagamento = pagamento_crud.update_pagamento(
        db, pagamento_id=pagamento_id, pagamento_update_data=pagamento_update_data, proprietario_id=current_user.id_user
    )

    if isinstance(updated_pagamento, str): # Tratamento de erro do CRUD
        if updated_pagamento == "ERRO_MES_REFERENCIA_FORMATO_UPDATE":
            raise HTTPException(status_code=400, detail="Formato do mês de referência inválido para atualização. Use 'AAAA-MM'.")
        raise HTTPException(status_code=400, detail="Erro ao atualizar pagamento: " + updated_pagamento)
    
    if updated_pagamento is None:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado ou não pertence a você para atualizar.")
    return updated_pagamento

@router.delete("/{pagamento_id}", response_model=schemas.Pagamento)
def delete_meu_pagamento(
    pagamento_id: int,
    db: Session = Depends(get_db),
    current_user: app_models.User = Depends(get_current_active_user)
):
    db_pagamento_deletado = pagamento_crud.delete_pagamento(
        db, pagamento_id=pagamento_id, proprietario_id=current_user.id_user
    )
    if db_pagamento_deletado is None:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado ou não pertence a você para deletar")
    return db_pagamento_deletado