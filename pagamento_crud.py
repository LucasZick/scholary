# pagamento_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from sqlalchemy import case, extract, or_ # Para extrair o ano do mes_referencia se necessário

import datetime
import app_models
import schemas
import contrato_servico_crud # Para validar o contrato

def create_pagamento(
    db: Session, pagamento_in: schemas.PagamentoCreate, proprietario_id: int
) -> Union[app_models.Pagamento, str]:
    
    # Validação: ContratoServico pertence ao proprietário?
    contrato = contrato_servico_crud.get_contrato_servico_por_id_e_proprietario(
        db, contrato_id=pagamento_in.id_contrato, proprietario_id=proprietario_id
    )
    if not contrato:
        return "ERRO_CONTRATO_INVALIDO"

    # Extrair ano do mes_referencia (formato 'AAAA-MM') para popular ano_referencia no modelo, se necessário
    try:
        ano_ref = int(pagamento_in.mes_referencia.split('-')[0])
    except:
        return "ERRO_MES_REFERENCIA_FORMATO" # Formato inválido para mes_referencia

    db_pagamento = app_models.Pagamento(
        id_contrato=pagamento_in.id_contrato,
        mes_referencia=pagamento_in.mes_referencia,
        ano_referencia=ano_ref, # Populando o campo do modelo
        data_vencimento=pagamento_in.data_vencimento,
        valor_nominal=pagamento_in.valor_nominal,
        valor_desconto=pagamento_in.valor_desconto,
        valor_acrescimo=pagamento_in.valor_acrescimo,
        valor_pago=pagamento_in.valor_pago,
        data_pagamento=pagamento_in.data_pagamento,
        metodo_pagamento=pagamento_in.metodo_pagamento,
        status_pagamento=pagamento_in.status_pagamento,
        id_transacao_gateway=pagamento_in.id_transacao_gateway,
        link_boleto_comprovante=pagamento_in.link_boleto_comprovante,
        observacoes_pagamento=pagamento_in.observacoes_pagamento
        # data_geracao é server_default
        # data_baixa é preenchido depois
    )
    db.add(db_pagamento)
    db.commit()
    db.refresh(db_pagamento)
    return db_pagamento

def get_pagamentos_por_contrato_e_proprietario(
    db: Session, contrato_id: int, proprietario_id: int, skip: int = 0, limit: int = 100
) -> Union[List[app_models.Pagamento], str]:
    
    # Primeiro, verifica se o contrato pertence ao proprietário
    contrato = contrato_servico_crud.get_contrato_servico_por_id_e_proprietario(
        db, contrato_id=contrato_id, proprietario_id=proprietario_id
    )
    if not contrato:
        return "ERRO_CONTRATO_INVALIDO"

    # Define a ordem de agrupamento por status
    status_order_expression = case(
        (app_models.Pagamento.status_pagamento.in_(['Pendente', 'Atrasado']), 1), # Grupo Não Pagos
        (app_models.Pagamento.status_pagamento == 'Pago', 2),                     # Grupo Pagos
        else_=3                                                                   # Outros status
    ).label("status_group")

    return db.query(app_models.Pagamento)\
        .filter(app_models.Pagamento.id_contrato == contrato_id)\
        .order_by(
            status_order_expression.asc(),  # Ordena pelos grupos (Não Pagos primeiro, depois Pagos)
            # Para pagamentos não pagos (Pendente/Atrasado), ordena por data de vencimento ascendente
            case(
                (app_models.Pagamento.status_pagamento.in_(['Pendente', 'Atrasado']), app_models.Pagamento.data_vencimento),
                else_=None # Não usa data_vencimento para ordenação primária de pagos aqui
            ).asc().nullsfirst(), # .nullsfirst() ou .nullslast() para tratar data_vencimento nula (não deve acontecer)
            
            # Para pagamentos pagos, ordena por data de pagamento descendente (mais recente primeiro)
            case(
                (app_models.Pagamento.status_pagamento == 'Pago', app_models.Pagamento.data_pagamento),
                else_=None # Não usa data_pagamento para ordenação de não pagos aqui
            ).desc().nullslast(), # .nullslast() para tratar data_pagamento nula (se um pago não tiver data_pagamento)

            app_models.Pagamento.id_pagamento.asc() # Ordenação final para garantir consistência
        )\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_pagamento_por_id_e_proprietario( # Verifica a propriedade através do contrato
    db: Session, pagamento_id: int, proprietario_id: int
) -> Optional[app_models.Pagamento]:
    # Este join é para garantir que o pagamento pertence a um contrato do proprietário
    pagamento = db.query(app_models.Pagamento).join(app_models.ContratoServico).filter(
        app_models.Pagamento.id_pagamento == pagamento_id,
        app_models.ContratoServico.id_proprietario_user == proprietario_id
    ).first()
    return pagamento

def get_pagamentos_atrasados_por_proprietario(
    db: Session, proprietario_id: int, skip: int = 0, limit: int = 100
) -> List[app_models.Pagamento]:
    """
    Busca pagamentos que estão com status 'Pendente' e data de vencimento passada,
    OU que já estão com status 'Atrasado', pertencentes ao proprietário.
    """
    hoje = datetime.date.today()
    return db.query(app_models.Pagamento)\
        .join(app_models.ContratoServico, app_models.Pagamento.id_contrato == app_models.ContratoServico.id_contrato)\
        .filter(app_models.ContratoServico.id_proprietario_user == proprietario_id)\
        .filter(
            or_(
                app_models.Pagamento.status_pagamento == "Atrasado",
                ( (app_models.Pagamento.status_pagamento == "Pendente") & (app_models.Pagamento.data_vencimento < hoje) ) # noqa E712
            )
        )\
        .order_by(app_models.Pagamento.data_vencimento.asc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def update_pagamento(
    db: Session, pagamento_id: int, pagamento_update_data: schemas.PagamentoUpdate, proprietario_id: int
) -> Optional[Union[app_models.Pagamento, str]]:
    
    db_pagamento = get_pagamento_por_id_e_proprietario(db, pagamento_id=pagamento_id, proprietario_id=proprietario_id)
    if not db_pagamento:
        return None # Ou "ERRO_PAGAMENTO_NAO_ENCONTRADO"

    update_data = pagamento_update_data.model_dump(exclude_unset=True)

    # Se mes_referencia for atualizado, atualizar também ano_referencia no modelo
    if "mes_referencia" in update_data:
        try:
            update_data["ano_referencia"] = int(update_data["mes_referencia"].split('-')[0])
        except:
            return "ERRO_MES_REFERENCIA_FORMATO_UPDATE"
    
    # Se o pagamento está sendo marcado como "Pago" e data_pagamento não foi fornecida, usar data atual
    if "status_pagamento" in update_data and update_data["status_pagamento"] == "Pago":
        if "data_pagamento" not in update_data or update_data["data_pagamento"] is None:
            update_data["data_pagamento"] = datetime.date.today() # type: ignore
        # Poderia também setar data_baixa aqui
        if "data_baixa" not in update_data or update_data["data_baixa"] is None:
             update_data["data_baixa"] = datetime.datetime.now(datetime.timezone.utc)


    for key, value in update_data.items():
        setattr(db_pagamento, key, value)
    
    db.add(db_pagamento)
    db.commit()
    db.refresh(db_pagamento)
    return db_pagamento


def atualizar_pagamentos_para_atrasado(db: Session) -> int:
    hoje = datetime.date.today()
    query = db.query(app_models.Pagamento).join(
        app_models.ContratoServico, 
        app_models.Pagamento.id_contrato == app_models.ContratoServico.id_contrato
    ).filter(
        or_(
            app_models.Pagamento.status_pagamento == "Atrasado", # Para re-processar se necessário (improvável)
            (
                (app_models.Pagamento.status_pagamento == "Pendente") &
                (app_models.Pagamento.data_vencimento < hoje)
            )
        )
    )
    query_para_atualizar = db.query(app_models.Pagamento).filter(
        app_models.Pagamento.status_pagamento == "Pendente",
        app_models.Pagamento.data_vencimento < hoje
    )
    
    num_atualizados = query_para_atualizar.update(
        {"status_pagamento": "Atrasado"}, 
        synchronize_session=False
    )
    
    if num_atualizados > 0:
        db.commit()
        
    return num_atualizados

def delete_pagamento(db: Session, pagamento_id: int, proprietario_id: int) -> Optional[app_models.Pagamento]:
    db_pagamento = get_pagamento_por_id_e_proprietario(db, pagamento_id=pagamento_id, proprietario_id=proprietario_id)
    if not db_pagamento:
        return None
    
    # Considerar regras de negócio antes de deletar um pagamento (ex: estorno?)
    # Por enquanto, deleção direta.
    
    db.delete(db_pagamento)
    db.commit()
    return db_pagamento
