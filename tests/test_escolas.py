# tests/test_escolas.py
import pytest
from fastapi.testclient import TestClient
import datetime
from typing import Dict # Para type hinting
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# NOTA: Mova estas helpers para conftest.py em um projeto real para evitar repetição!

def get_operator_token(client: TestClient, email_prefix: str) -> Dict[str, str]:
    """Registra um novo operador e retorna o cabeçalho de autorização com o token."""
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword_escola" # Senha específica para este helper
    
    reg_payload = {"email": email, "password": password, "nome_completo": f"Operador {email_prefix} Escolas"}
    # Tenta registrar, não falha se já existir para permitir que o login funcione
    client.post("/users/register", json=reg_payload) 
    
    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Falha ao obter token para {email} no helper de escolas: {login_response.text} (Registro payload: {reg_payload})")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_string(prefix: str = "test_esc_") -> str:
    """Gera uma string pseudo-única para testes."""
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

def generate_unique_cnpj(prefix: str = "112223330001") -> str:
    """Gera um CNPJ pseudo-único para testes."""
    # Formato XX.XXX.XXX/XXXX-XX (18 chars)
    # Nosso modelo tem String(18) para CNPJ.
    # O gerador abaixo é simples e pode não ser um CNPJ válido, ajuste se precisar de validação de formato.
    suffix = str(datetime.datetime.now().timestamp()).replace('.', '')[-2:]
    return f"{prefix}{suffix}"[-18:]


# --- Testes para Escolas ---

def test_create_escola_success(client: TestClient):
    headers = get_operator_token(client, "op_esc_create")
    nome_escola = generate_unique_string("Escola Sucesso ")
    cnpj_escola = generate_unique_cnpj("01")
    escola_data = {
        "nome_escola": nome_escola,
        "endereco_completo": "Rua do Sucesso, 100",
        "cnpj": cnpj_escola,
        "telefone_escola": "1122334455",
        "nome_contato_escola": "Diretor Sucesso",
        "email_contato_escola": f"{generate_unique_string('contato_')}@sucesso.com"
    }
    response = client.post("/escolas", headers=headers, json=escola_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nome_escola"] == nome_escola
    assert data["cnpj"] == cnpj_escola
    assert "id_escola" in data

def test_create_escola_unauthenticated(client: TestClient):
    escola_data = {
        "nome_escola": "Escola Sem Auth",
        "endereco_completo": "Rua Desconhecida, 0",
        "cnpj": generate_unique_cnpj("02")
    }
    response = client.post("/escolas", json=escola_data)
    assert response.status_code == 401, response.text

def test_create_escola_missing_required_fields(client: TestClient):
    headers = get_operator_token(client, "op_esc_missing")
    # Faltando nome_escola e endereco_completo que são obrigatórios no schema EscolaBase/EscolaCreate
    escola_data = {"cnpj": generate_unique_cnpj("03")}
    response = client.post("/escolas", headers=headers, json=escola_data)
    assert response.status_code == 422, response.text # Erro de validação Pydantic

def test_create_escola_duplicate_nome_for_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_esc_dupnome")
    nome_escola_unico = generate_unique_string("Escola Nome Unico ")
    
    client.post("/escolas", headers=headers, json={
        "nome_escola": nome_escola_unico, "endereco_completo": "End A", "cnpj": generate_unique_cnpj("04A")
    })
    response_duplicate = client.post("/escolas", headers=headers, json={
        "nome_escola": nome_escola_unico, "endereco_completo": "End B", "cnpj": generate_unique_cnpj("04B")
    })
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui uma escola com o nome" in response_duplicate.json()["detail"]

def test_create_escola_duplicate_cnpj_for_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_esc_dupcnpj")
    cnpj_unico = generate_unique_cnpj("05")

    client.post("/escolas", headers=headers, json={
        "nome_escola": generate_unique_string("Escola CNPJ Unico A "), "endereco_completo": "End C", "cnpj": cnpj_unico
    })
    response_duplicate = client.post("/escolas", headers=headers, json={
        "nome_escola": generate_unique_string("Escola CNPJ Unico B "), "endereco_completo": "End D", "cnpj": cnpj_unico
    })
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui uma escola com o CNPJ" in response_duplicate.json()["detail"]


def test_list_minhas_escolas(client: TestClient):
    headers = get_operator_token(client, "op_esc_list")
    nome_escola_para_lista = generate_unique_string("Escola para Lista ")
    client.post("/escolas", headers=headers, json={
        "nome_escola": nome_escola_para_lista, "endereco_completo": "End Lista", "cnpj": generate_unique_cnpj("06")
    })
    response = client.get("/escolas", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1 # Pode haver outras escolas criadas por este operador em testes anteriores na mesma sessão de token
    assert any(e["nome_escola"] == nome_escola_para_lista for e in data)

def test_get_minha_escola_by_id_success(client: TestClient):
    headers = get_operator_token(client, "op_esc_getid")
    nome_escola_get = generate_unique_string("Escola para GET ")
    create_response = client.post("/escolas", headers=headers, json={
        "nome_escola": nome_escola_get, "endereco_completo": "End GET", "cnpj": generate_unique_cnpj("07")
    })
    escola_id = create_response.json()["id_escola"]
    
    response = client.get(f"/escolas/{escola_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_escola"] == escola_id
    assert data["nome_escola"] == nome_escola_get

def test_get_escola_nao_existente(client: TestClient):
    headers = get_operator_token(client, "op_esc_get_naoexiste")
    response = client.get("/escolas/9999999", headers=headers) # ID improvável
    assert response.status_code == 404, response.text

def test_update_minha_escola_success(client: TestClient):
    headers = get_operator_token(client, "op_esc_update")
    create_response = client.post("/escolas", headers=headers, json={
        "nome_escola": generate_unique_string("Escola Original "), "endereco_completo": "End Original", "cnpj": generate_unique_cnpj("08")
    })
    escola_id = create_response.json()["id_escola"]
    
    novo_nome = generate_unique_string("Escola ATUALIZADA ")
    update_data = {"nome_escola": novo_nome, "telefone_escola": "9876543210"}
    response = client.put(f"/escolas/{escola_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_escola"] == escola_id
    assert data["nome_escola"] == novo_nome
    assert data["telefone_escola"] == "9876543210"

def test_update_escola_para_nome_duplicado(client: TestClient):
    headers = get_operator_token(client, "op_esc_upd_dupnome")
    nome_existente = generate_unique_string("Nome Existente Update ")
    client.post("/escolas", headers=headers, json={ # Escola 1
        "nome_escola": nome_existente, "endereco_completo": "End 1", "cnpj": generate_unique_cnpj("09A")
    })
    escola2_resp = client.post("/escolas", headers=headers, json={ # Escola 2
        "nome_escola": generate_unique_string("Escola para ser Atualizada "), "endereco_completo": "End 2", "cnpj": generate_unique_cnpj("09B")
    })
    escola2_id = escola2_resp.json()["id_escola"]

    # Tenta atualizar Escola 2 para ter o mesmo nome da Escola 1
    response = client.put(f"/escolas/{escola2_id}", headers=headers, json={"nome_escola": nome_existente})
    assert response.status_code == 400, response.text
    assert "Você já possui outra escola com o nome" in response.json()["detail"]


def test_delete_minha_escola_success(client: TestClient):
    headers = get_operator_token(client, "op_esc_delete")
    create_response = client.post("/escolas", headers=headers, json={
        "nome_escola": generate_unique_string("Escola para Deletar "), "endereco_completo": "End Deletar", "cnpj": generate_unique_cnpj("10")
    })
    escola_id = create_response.json()["id_escola"]
    
    response = client.delete(f"/escolas/{escola_id}", headers=headers)
    assert response.status_code == 200, response.text # Router retorna o objeto deletado com 200
    
    get_response = client.get(f"/escolas/{escola_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text


def test_escola_data_isolation_completo(client: TestClient):
    # Operador A
    headers_op_a = get_operator_token(client, "opA_esc_iso_full")
    escola_a_data = {
        "nome_escola": generate_unique_string("Escola OpA Full "),
        "endereco_completo": "Rua A Full",
        "cnpj": generate_unique_cnpj("11A")
    }
    create_resp_a = client.post("/escolas", headers=headers_op_a, json=escola_a_data)
    assert create_resp_a.status_code == 201, create_resp_a.text
    escola_op_a = schemas.Escola(**create_resp_a.json())

    # Operador B
    headers_op_b = get_operator_token(client, "opB_esc_iso_full")

    # 1. Operador B tenta LER a escola do Operador A pelo ID
    response_get_b_for_a = client.get(f"/escolas/{escola_op_a.id_escola}", headers=headers_op_b)
    assert response_get_b_for_a.status_code == 404

    # 2. Operador B lista suas escolas (não deve ver a do Operador A)
    response_list_b = client.get("/escolas", headers=headers_op_b)
    assert response_list_b.status_code == 200
    escolas_op_b = response_list_b.json()
    assert not any(e["id_escola"] == escola_op_a.id_escola for e in escolas_op_b)

    # 3. Operador B tenta ATUALIZAR a escola do Operador A
    update_data_b_for_a = {"nome_escola": "Tentativa Update por B"}
    response_put_b_for_a = client.put(f"/escolas/{escola_op_a.id_escola}", headers=headers_op_b, json=update_data_b_for_a)
    assert response_put_b_for_a.status_code == 404 # Ou 403 se você implementar essa distinção

    # 4. Operador B tenta DELETAR a escola do Operador A
    response_delete_b_for_a = client.delete(f"/escolas/{escola_op_a.id_escola}", headers=headers_op_b)
    assert response_delete_b_for_a.status_code == 404 # Ou 403

    # 5. Operador A ainda consegue ler sua escola (não foi afetada pelas tentativas do Op B)
    response_get_a_for_a = client.get(f"/escolas/{escola_op_a.id_escola}", headers=headers_op_a)
    assert response_get_a_for_a.status_code == 200
    assert response_get_a_for_a.json()["nome_escola"] == escola_op_a.nome_escola