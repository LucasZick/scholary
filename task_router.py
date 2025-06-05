# task_router.py
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional # Para Optional no Header
import os

from core_utils import get_db # Sua dependência de sessão de DB
import pagamento_crud # Seu CRUD de pagamentos

router = APIRouter(
    prefix="/tasks", # Prefixo para todas as rotas de tarefas
    tags=["Tarefas Agendadas"],
    responses={403: {"description": "Acesso não autorizado"}}
)

# Carrega a chave secreta do cron job das variáveis de ambiente
# Certifique-se de definir CRON_JOB_SECRET no seu .env e no ambiente do servidor
CRON_JOB_SECRET = os.getenv("CRON_JOB_SECRET") 

@router.post("/update-overdue-payments", 
             summary="Atualiza pagamentos pendentes para atrasados",
             description="Endpoint para ser chamado por um cron job. Requer header 'X-Cron-Secret'.")
async def trigger_update_overdue_payments(
    db: Session = Depends(get_db),
    x_cron_secret: Optional[str] = Header(None, description="Chave secreta para autorizar o cron job.")
):
    if not CRON_JOB_SECRET or x_cron_secret != CRON_JOB_SECRET:
        print("LOG ALERTA: Tentativa de acesso não autorizado ao cron job de pagamentos.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso não autorizado."
        )

    try:
        print("LOG INFO: Iniciando tarefa de atualização de pagamentos atrasados...")
        num_atualizados = pagamento_crud.atualizar_pagamentos_para_atrasado(db)
        print(f"LOG INFO: Tarefa de pagamentos atrasados concluída. {num_atualizados} pagamentos atualizados para 'Atrasado'.")
        return {"message": "Tarefa de atualização de pagamentos atrasados executada com sucesso.", "atualizados": num_atualizados}
    except Exception as e:
        print(f"LOG ERRO: Erro na tarefa de atualização de pagamentos atrasados: {e}")
        # Em um sistema de produção, você logaria isso de forma mais robusta (ex: Sentry, arquivo de log)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno ao executar a tarefa: {str(e)}"
        )