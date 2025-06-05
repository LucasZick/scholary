# aluno_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional, Union # <-- ADICIONE Union AQUI

import app_models
import schemas
import escola_crud # Para validar a escola
import responsavel_crud # Para validar o responsável

def create_aluno(
    db: Session, aluno_in: schemas.AlunoCreate, proprietario_id: int
) -> Union[app_models.Aluno, str] : # Pode retornar o Aluno ou uma string de erro
    
    # Validação: Escola pertence ao proprietário?
    escola = escola_crud.get_escola_por_id_e_proprietario(
        db, escola_id=aluno_in.id_escola, proprietario_id=proprietario_id
    )
    if not escola:
        return "ERRO_ESCOLA_INVALIDA"

    # Validação: Responsável Principal pertence ao proprietário?
    responsavel_principal = responsavel_crud.get_responsavel_por_id_e_proprietario(
        db, responsavel_id=aluno_in.id_responsavel_principal, proprietario_id=proprietario_id
    )
    if not responsavel_principal:
        return "ERRO_RESPONSAVEL_PRINCIPAL_INVALIDO"

    # Validação: Responsável Secundário (se houver) pertence ao proprietário?
    if aluno_in.id_responsavel_secundario:
        responsavel_secundario = responsavel_crud.get_responsavel_por_id_e_proprietario(
            db, responsavel_id=aluno_in.id_responsavel_secundario, proprietario_id=proprietario_id
        )
        if not responsavel_secundario:
            return "ERRO_RESPONSAVEL_SECUNDARIO_INVALIDO"
            
    db_aluno = app_models.Aluno(
        **aluno_in.model_dump(), 
        id_proprietario_user=proprietario_id
    )
    db.add(db_aluno)
    db.commit()
    db.refresh(db_aluno)
    return db_aluno

def get_alunos_por_proprietario(db: Session, proprietario_id: int, skip: int = 0, limit: int = 100) -> List[app_models.Aluno]:
    return db.query(app_models.Aluno).filter(app_models.Aluno.id_proprietario_user == proprietario_id).offset(skip).limit(limit).all()

def get_aluno_por_id_e_proprietario(db: Session, aluno_id: int, proprietario_id: int) -> Optional[app_models.Aluno]:
    return db.query(app_models.Aluno).filter(
        app_models.Aluno.id_aluno == aluno_id,
        app_models.Aluno.id_proprietario_user == proprietario_id
    ).first()

def update_aluno(
    db: Session, aluno_id: int, aluno_update_data: schemas.AlunoUpdate, proprietario_id: int
) -> Union[app_models.Aluno, str, None]:
    db_aluno = get_aluno_por_id_e_proprietario(db, aluno_id=aluno_id, proprietario_id=proprietario_id)
    if not db_aluno:
        return None # Ou "ERRO_ALUNO_NAO_ENCONTRADO"

    update_data = aluno_update_data.model_dump(exclude_unset=True)

    # Validações se IDs de escola ou responsáveis forem alterados
    if "id_escola" in update_data and update_data["id_escola"] != db_aluno.id_escola:
        escola = escola_crud.get_escola_por_id_e_proprietario(db, escola_id=update_data["id_escola"], proprietario_id=proprietario_id)
        if not escola: return "ERRO_ESCOLA_INVALIDA_UPDATE"
    
    if "id_responsavel_principal" in update_data and update_data["id_responsavel_principal"] != db_aluno.id_responsavel_principal:
        resp_p = responsavel_crud.get_responsavel_por_id_e_proprietario(db, responsavel_id=update_data["id_responsavel_principal"], proprietario_id=proprietario_id)
        if not resp_p: return "ERRO_RESP_P_INVALIDO_UPDATE"

    if "id_responsavel_secundario" in update_data and update_data["id_responsavel_secundario"] != db_aluno.id_responsavel_secundario:
        if update_data["id_responsavel_secundario"] is not None: # Se estiver tentando setar um novo
            resp_s = responsavel_crud.get_responsavel_por_id_e_proprietario(db, responsavel_id=update_data["id_responsavel_secundario"], proprietario_id=proprietario_id)
            if not resp_s: return "ERRO_RESP_S_INVALIDO_UPDATE"
        # Se for None, está ok (removendo o secundário)

    for key, value in update_data.items():
        setattr(db_aluno, key, value)
    
    db.add(db_aluno)
    db.commit()
    db.refresh(db_aluno)
    return db_aluno

def delete_aluno(db: Session, aluno_id: int, proprietario_id: int) -> Optional[app_models.Aluno]:
    db_aluno = get_aluno_por_id_e_proprietario(db, aluno_id=aluno_id, proprietario_id=proprietario_id)
    if not db_aluno:
        return None
    db.delete(db_aluno)
    db.commit()
    return db_aluno