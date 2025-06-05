# contrato_servico_crud.py
from sqlalchemy.orm import Session
from sqlalchemy import extract # Não estamos usando extract diretamente aqui, mas pode ser útil
from typing import List, Optional, Tuple, Union
from datetime import date, timedelta # datetime adicionado para clareza no Pagamento
from decimal import Decimal
import datetime

# Se você decidir usar dateutil para manipulação de datas mais complexas:
# from dateutil.relativedelta import relativedelta

import app_models # Seus modelos SQLAlchemy
import schemas    # Seus schemas Pydantic
import aluno_crud # Necessário para validar o aluno
import responsavel_crud # Necessário para validar o responsável

# Função auxiliar para calcular o próximo mês
def proximo_mes(ano: int, mes: int) -> Tuple[int, int]:
    mes += 1
    if mes > 12:
        mes = 1
        ano += 1
    return ano, mes

def create_contrato_servico(
    db: Session, contrato_in: schemas.ContratoServicoCreate, proprietario_id: int
) -> Union[app_models.ContratoServico, str]:
    
    # Validação: Aluno pertence ao proprietário?
    aluno = aluno_crud.get_aluno_por_id_e_proprietario(
        db, aluno_id=contrato_in.id_aluno, proprietario_id=proprietario_id
    )
    if not aluno:
        return "ERRO_ALUNO_INVALIDO"

    # Validação: Responsável Financeiro pertence ao proprietário?
    responsavel = responsavel_crud.get_responsavel_por_id_e_proprietario(
        db, responsavel_id=contrato_in.id_responsavel_financeiro, proprietario_id=proprietario_id
    )
    if not responsavel:
        return "ERRO_RESPONSAVEL_INVALIDO"

    # (Opcional) Validação adicional: O responsável financeiro é um dos responsáveis do aluno?
    if aluno.id_responsavel_principal != responsavel.id_responsavel and \
        (aluno.id_responsavel_secundario is None or aluno.id_responsavel_secundario != responsavel.id_responsavel):
        return "ERRO_RESPONSAVEL_NAO_ASSOCIADO_AO_ALUNO" # Ou uma regra de negócio diferente

    data_inicio_contrato = contrato_in.data_inicio_contrato
    data_fim_efetiva_para_pagamentos: date

    if contrato_in.data_fim_contrato is None:
        ano_inicio = data_inicio_contrato.year
        data_fim_efetiva_para_pagamentos = date(ano_inicio, 12, 31)
    else:
        data_fim_efetiva_para_pagamentos = contrato_in.data_fim_contrato
        if data_fim_efetiva_para_pagamentos < data_inicio_contrato:
            return "ERRO_DATA_FIM_ANTERIOR_DATA_INICIO"

    db_contrato = app_models.ContratoServico(
        # ... (campos do contrato como antes) ...
        id_aluno=contrato_in.id_aluno,
        id_responsavel_financeiro=contrato_in.id_responsavel_financeiro,
        data_inicio_contrato=data_inicio_contrato,
        data_fim_contrato=contrato_in.data_fim_contrato,
        valor_mensal=contrato_in.valor_mensal,
        dia_vencimento_mensalidade=contrato_in.dia_vencimento_mensalidade,
        tipo_servico_contratado=contrato_in.tipo_servico_contratado,
        status_contrato=contrato_in.status_contrato or "Ativo",
        observacoes_contrato=contrato_in.observacoes_contrato,
        id_proprietario_user=proprietario_id
    )
    
    pagamentos_a_criar = []
    mes_iterador = date(data_inicio_contrato.year, data_inicio_contrato.month, 1)
    hoje = datetime.date.today() # Data de hoje para comparar vencimentos

    while mes_iterador <= data_fim_efetiva_para_pagamentos:
        ano_ref = mes_iterador.year
        mes_ref_int = mes_iterador.month
        
        try:
            data_venc = date(ano_ref, mes_ref_int, contrato_in.dia_vencimento_mensalidade)
        except ValueError: 
            if mes_ref_int == 12:
                ultimo_dia_mes = date(ano_ref, mes_ref_int, 31)
            else:
                ultimo_dia_mes = date(ano_ref, mes_ref_int + 1, 1) - timedelta(days=1)
            data_venc = ultimo_dia_mes
        
        status_inicial_pagamento = "Pendente"
        # Define como "Atrasado" na criação se a data de vencimento já passou e o status seria "Pendente"
        if data_venc < hoje:
            status_inicial_pagamento = "Atrasado"

        novo_pagamento_obj = app_models.Pagamento(
            mes_referencia=f"{ano_ref:04d}-{mes_ref_int:02d}",
            ano_referencia=ano_ref,
            data_vencimento=data_venc,
            valor_nominal=contrato_in.valor_mensal,
            status_pagamento=status_inicial_pagamento, # Status definido aqui
        )
        pagamentos_a_criar.append(novo_pagamento_obj)

        ano_ref, mes_ref_int = proximo_mes(ano_ref, mes_ref_int)
        mes_iterador = date(ano_ref, mes_ref_int, 1)

    db_contrato.pagamentos = pagamentos_a_criar

    try:
        db.add(db_contrato)
        db.commit()
        db.refresh(db_contrato)
        return db_contrato
    except Exception as e:
        db.rollback()
        print(f"LOG ERRO CRUD: Erro ao criar contrato e pagamentos: {e}")
        return "ERRO_INESPERADO_AO_SALVAR_CONTRATO_PAGAMENTOS"


def get_contratos_servico_por_proprietario(
    db: Session, proprietario_id: int, skip: int = 0, limit: int = 100
) -> List[app_models.ContratoServico]:
    return db.query(app_models.ContratoServico).filter(
        app_models.ContratoServico.id_proprietario_user == proprietario_id # Nome padronizado
    ).offset(skip).limit(limit).all()

def get_contrato_servico_por_id_e_proprietario(
    db: Session, contrato_id: int, proprietario_id: int
) -> Optional[app_models.ContratoServico]:
    return db.query(app_models.ContratoServico).filter(
        app_models.ContratoServico.id_contrato == contrato_id,
        app_models.ContratoServico.id_proprietario_user == proprietario_id # Nome padronizado
    ).first()

def update_contrato_servico(
    db: Session, contrato_id: int, contrato_update_data: schemas.ContratoServicoUpdate, proprietario_id: int
) -> Optional[Union[app_models.ContratoServico, str]]:
    
    # Busca o contrato original para garantir que pertence ao proprietário
    db_contrato = db.query(app_models.ContratoServico).filter(
        app_models.ContratoServico.id_contrato == contrato_id,
        app_models.ContratoServico.id_proprietario_user == proprietario_id
    ).first()

    if not db_contrato:
        return "ERRO_CONTRATO_NAO_ENCONTRADO"

    update_data = contrato_update_data.model_dump(exclude_unset=True)

    # --- Validações de FKs se forem alteradas (se o schema ContratoServicoUpdate permitir) ---
    if "id_aluno" in update_data and update_data["id_aluno"] != db_contrato.id_aluno:
        aluno = aluno_crud.get_aluno_por_id_e_proprietario(db, aluno_id=update_data["id_aluno"], proprietario_id=proprietario_id)
        if not aluno: return "ERRO_ALUNO_INVALIDO_UPDATE"
    
    if "id_responsavel_financeiro" in update_data and update_data["id_responsavel_financeiro"] != db_contrato.id_responsavel_financeiro:
        responsavel = responsavel_crud.get_responsavel_por_id_e_proprietario(db, responsavel_id=update_data["id_responsavel_financeiro"], proprietario_id=proprietario_id)
        if not responsavel: return "ERRO_RESPONSAVEL_INVALIDO_UPDATE"

    # Aplica as atualizações ao objeto contrato em memória primeiro
    # Isso é importante para que a geração de novos pagamentos use os valores atualizados do contrato
    for key, value in update_data.items():
        setattr(db_contrato, key, value)

    # --- Lógica de Sincronização de Pagamentos ---
    data_fim_contrato_payload = update_data.get("data_fim_contrato") # Pode ser None se enviado para limpar
    data_fim_contrato_foi_enviada = "data_fim_contrato" in update_data # True se a chave estava no payload
    
    valor_mensal_mudou = "valor_mensal" in update_data
    dia_vencimento_mudou = "dia_vencimento_mensalidade" in update_data
    status_contrato_mudou = "status_contrato" in update_data

    # Só recalcula pagamentos se um campo relevante para eles mudou, ou se o status do contrato mudou para Cancelado/Suspenso
    if data_fim_contrato_foi_enviada or valor_mensal_mudou or dia_vencimento_mudou or \
       (status_contrato_mudou and db_contrato.status_contrato in ["Cancelado", "Suspenso"]):

        pagamentos_existentes_nao_pagos = db.query(app_models.Pagamento).filter(
            app_models.Pagamento.id_contrato == db_contrato.id_contrato,
            app_models.Pagamento.status_pagamento.in_(['Pendente', 'Atrasado'])
        ).order_by(app_models.Pagamento.mes_referencia.asc()).all()

        # 1. Se o contrato foi cancelado/suspenso, cancela todos os pagamentos não pagos
        if status_contrato_mudou and db_contrato.status_contrato in ["Cancelado", "Suspenso"]:
            for pag in pagamentos_existentes_nao_pagos:
                pag.status_pagamento = "Cancelado" 
                db.add(pag)
            # Não gera novos pagamentos se o contrato foi cancelado/suspenso.
        
        # 2. Lógica para data_fim_contrato, valor_mensal e dia_vencimento (só se contrato não foi cancelado/suspenso)
        elif db_contrato.status_contrato not in ["Cancelado", "Suspenso"]:
            data_inicio_contrato = db_contrato.data_inicio_contrato # Pega do contrato já potencialmente atualizado
            data_fim_efetiva_para_pagamentos: date

            # Usa a data_fim_contrato do objeto db_contrato (que já foi atualizado em memória se veio no payload)
            if db_contrato.data_fim_contrato is None:
                ano_inicio = data_inicio_contrato.year
                data_fim_efetiva_para_pagamentos = date(ano_inicio, 12, 31)
            else:
                data_fim_efetiva_para_pagamentos = db_contrato.data_fim_contrato
                if data_fim_efetiva_para_pagamentos < data_inicio_contrato:
                    db.rollback() 
                    return "ERRO_DATA_FIM_ANTERIOR_DATA_INICIO_UPDATE"

            pagamentos_a_manter_ou_atualizar = []
            for pag in pagamentos_existentes_nao_pagos:
                # Converte mes_referencia 'AAAA-MM' para um objeto date (primeiro dia do mês)
                mes_ref_pag_date = date(int(pag.mes_referencia[:4]), int(pag.mes_referencia[5:]), 1)
                if mes_ref_pag_date <= data_fim_efetiva_para_pagamentos:
                    pagamentos_a_manter_ou_atualizar.append(pag)
                else:
                    db.delete(pag) # Deleta pagamentos que ficaram fora do novo período

            # Atualiza valor e data de vencimento dos pagamentos mantidos
            if valor_mensal_mudou or dia_vencimento_mudou:
                hoje = date.today()
                for pag in pagamentos_a_manter_ou_atualizar:
                    if valor_mensal_mudou:
                        pag.valor_nominal = db_contrato.valor_mensal 
                    
                    if dia_vencimento_mudou:
                        try:
                            nova_data_venc = date(
                                pag.ano_referencia, 
                                int(pag.mes_referencia[5:]),
                                db_contrato.dia_vencimento_mensalidade
                            )
                        except ValueError:
                            mes_pagamento = int(pag.mes_referencia[5:])
                            if mes_pagamento == 12:
                                ultimo_dia_mes = date(pag.ano_referencia, mes_pagamento, 31)
                            else:
                                ultimo_dia_mes = date(pag.ano_referencia, mes_pagamento + 1, 1) - timedelta(days=1)
                            nova_data_venc = ultimo_dia_mes
                        pag.data_vencimento = nova_data_venc
                        
                        # Reavalia status (não mexe em "Pago" ou "Cancelado", mas estamos em _nao_pagos)
                        if pag.data_vencimento < hoje:
                            pag.status_pagamento = "Atrasado"
                        else:
                            pag.status_pagamento = "Pendente"
                    db.add(pag)

            # Gera novos pagamentos se o contrato foi estendido
            ultimo_mes_gerado_obj = None
            if pagamentos_a_manter_ou_atualizar:
                pagamentos_a_manter_ou_atualizar.sort(key=lambda p: p.mes_referencia) # Garante a ordem
                ultimo_mes_gerado_str = pagamentos_a_manter_ou_atualizar[-1].mes_referencia
                ultimo_mes_gerado_obj = date(int(ultimo_mes_gerado_str[:4]), int(ultimo_mes_gerado_str[5:]), 1)
            
            mes_iterador_para_novos: date
            if ultimo_mes_gerado_obj:
                ano_seguinte, mes_seguinte = proximo_mes(ultimo_mes_gerado_obj.year, ultimo_mes_gerado_obj.month)
                mes_iterador_para_novos = date(ano_seguinte, mes_seguinte, 1)
            else: 
                mes_iterador_para_novos = date(data_inicio_contrato.year, data_inicio_contrato.month, 1)

            novos_pagamentos_para_adicionar_na_sessao = []
            while mes_iterador_para_novos <= data_fim_efetiva_para_pagamentos:
                ano_ref = mes_iterador_para_novos.year
                mes_ref_int = mes_iterador_para_novos.month
                
                # Verifica se já existe um pagamento para este mes_referencia (dos mantidos)
                # para não criar duplicados se a lógica de deleção/manutenção não foi perfeita.
                # Esta é uma segurança extra.
                ja_existe_para_este_mes = any(
                    p.mes_referencia == f"{ano_ref:04d}-{mes_ref_int:02d}" for p in pagamentos_a_manter_ou_atualizar
                )
                if ja_existe_para_este_mes:
                    ano_ref, mes_ref_int = proximo_mes(ano_ref, mes_ref_int)
                    mes_iterador_para_novos = date(ano_ref, mes_ref_int, 1)
                    continue


                try:
                    data_venc = date(ano_ref, mes_ref_int, db_contrato.dia_vencimento_mensalidade)
                except ValueError:
                    if mes_ref_int == 12: ultimo_dia_mes = date(ano_ref, mes_ref_int, 31)
                    else: ultimo_dia_mes = date(ano_ref, mes_ref_int + 1, 1) - timedelta(days=1)
                    data_venc = ultimo_dia_mes
                
                status_inicial_novo_pag = "Pendente"
                if data_venc < date.today():
                    status_inicial_novo_pag = "Atrasado"

                novo_pagamento_obj = app_models.Pagamento(
                    id_contrato=db_contrato.id_contrato, 
                    mes_referencia=f"{ano_ref:04d}-{mes_ref_int:02d}",
                    ano_referencia=ano_ref,
                    data_vencimento=data_venc,
                    valor_nominal=db_contrato.valor_mensal, 
                    status_pagamento=status_inicial_novo_pag,
                )
                novos_pagamentos_para_adicionar_na_sessao.append(novo_pagamento_obj)

                ano_ref, mes_ref_int = proximo_mes(ano_ref, mes_ref_int)
                mes_iterador_para_novos = date(ano_ref, mes_ref_int, 1)
            
            if novos_pagamentos_para_adicionar_na_sessao:
                db.add_all(novos_pagamentos_para_adicionar_na_sessao)
    
    try:
        db.commit()
        db.refresh(db_contrato)
        # Para garantir que o relacionamento db_contrato.pagamentos esteja atualizado com todas as mudanças
        db.refresh(db_contrato, attribute_names=['pagamentos'])
        return db_contrato
    except Exception as e:
        db.rollback()
        print(f"LOG ERRO CRUD: Erro final ao atualizar contrato e pagamentos: {e}")
        return "ERRO_INESPERADO_AO_ATUALIZAR_CONTRATO_PAGAMENTOS"


def delete_contrato_servico(db: Session, contrato_id: int, proprietario_id: int) -> Optional[app_models.ContratoServico]:
    db_contrato = get_contrato_servico_por_id_e_proprietario(
        db, contrato_id=contrato_id, proprietario_id=proprietario_id
    )
    if not db_contrato:
        return None
    
    # Pagamentos associados serão deletados automaticamente devido ao cascade="all, delete-orphan"
    # no relacionamento ContratoServico.pagamentos no modelo SQLAlchemy.
    db.delete(db_contrato)
    db.commit()
    return db_contrato # Retorna o objeto deletado (desanexado da sessão)