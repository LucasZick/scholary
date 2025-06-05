# tests/test_responsaveis.py
import pytest
from fastapi.testclient import TestClient
import datetime # Para gerar dados únicos
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# Idealmente, get_operator_token estaria em conftest.py para ser reutilizado.
# Vou incluí-la aqui para este exemplo ser autocontido por enquanto.
def get_operator_token(client: TestClient, email_prefix: str) -> dict:
    """Registra um novo operador e retorna o cabeçalho de autorização com o token."""
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword"
    
    reg_response = client.post(
        "/users/register",
        json={"email": email, "password": password, "nome_completo": f"Operador {email_prefix}"},
    )
    if reg_response.status_code != 201:
        # Se o usuário já existir de uma execução anterior (sem rollback perfeito entre módulos de teste),
        # tentamos logar diretamente. Em um setup ideal com DB limpo por teste, isso não seria necessário.
        pass # Deixa o login abaixo tentar
    
    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Falha ao obter token para {email} durante o setup do teste: {login_response.text} (Registro status: {reg_response.status_code})")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_cpf(prefix: str = "123456789") -> str:
    """Gera um CPF pseudo-único para testes."""
    suffix = str(datetime.datetime.now().timestamp()).replace('.', '')[-2:]
    return f"{prefix}{suffix}"[-11:] # Garante 11 dígitos

def generate_unique_email(prefix: str = "responsavel_test") -> str:
    """Gera um email pseudo-único para testes."""
    return f"{prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"

# --- Testes para Responsáveis ---

def test_create_responsavel_success(client: TestClient):
    headers = get_operator_token(client, "op_resp_create")
    responsavel_data = {
        "nome_completo": "Responsável Teste Bem Sucedido",
        "cpf": generate_unique_cpf("001"),
        "email": generate_unique_email("resp_success"),
        "telefone_principal": "11987654321",
    }
    response = client.post("/responsaveis", headers=headers, json=responsavel_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nome_completo"] == responsavel_data["nome_completo"]
    assert data["cpf"] == responsavel_data["cpf"]
    assert data["email"] == responsavel_data["email"]
    assert "id_responsavel" in data

def test_create_responsavel_unauthenticated(client: TestClient):
    responsavel_data = {
        "nome_completo": "Responsável Sem Auth",
        "cpf": generate_unique_cpf("002"),
        "email": generate_unique_email("resp_noauth"),
        "telefone_principal": "22987654321",
    }
    response = client.post("/responsaveis", json=responsavel_data)
    assert response.status_code == 401, response.text

def test_create_responsavel_duplicate_cpf_for_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_resp_dupcpf")
    cpf_unico = generate_unique_cpf("003")
    
    client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável Original CPF",
            "cpf": cpf_unico,
            "email": generate_unique_email("resp_orig_cpf"),
            "telefone_principal": "331234567",
        },
    )
    
    response_duplicate = client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável Duplicado CPF",
            "cpf": cpf_unico, # Mesmo CPF
            "email": generate_unique_email("resp_dup_cpf"), # Email diferente
            "telefone_principal": "337654321",
        },
    )
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui um responsável com o CPF" in response_duplicate.json()["detail"]

def test_create_responsavel_duplicate_email_for_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_resp_dupemail")
    email_unico = generate_unique_email("resp_orig_email")

    client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável Original Email",
            "cpf": generate_unique_cpf("004"),
            "email": email_unico,
            "telefone_principal": "441234567",
        },
    )
    
    response_duplicate = client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável Duplicado Email",
            "cpf": generate_unique_cpf("005"), # CPF diferente
            "email": email_unico, # Mesmo Email
            "telefone_principal": "447654321",
        },
    )
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui um responsável com o email" in response_duplicate.json()["detail"]


def test_list_meus_responsaveis(client: TestClient):
    headers = get_operator_token(client, "op_resp_list")
    # Cria um responsável para garantir que a lista não esteja vazia
    client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável para Listagem",
            "cpf": generate_unique_cpf("006"),
            "email": generate_unique_email("resp_list"),
            "telefone_principal": "551234567",
        },
    )
    
    response = client.get("/responsaveis", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["nome_completo"] == "Responsável para Listagem" for r in data)

def test_get_meu_responsavel_by_id(client: TestClient):
    headers = get_operator_token(client, "op_resp_getid")
    create_response = client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável para GET ID",
            "cpf": generate_unique_cpf("007"),
            "email": generate_unique_email("resp_getid"),
            "telefone_principal": "661234567",
        },
    )
    responsavel_id = create_response.json()["id_responsavel"]
    
    response = client.get(f"/responsaveis/{responsavel_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_responsavel"] == responsavel_id
    assert data["nome_completo"] == "Responsável para GET ID"

def test_get_responsavel_nao_existente(client: TestClient):
    headers = get_operator_token(client, "op_resp_getid_naoexiste")
    response = client.get("/responsaveis/999999", headers=headers) # ID que provavelmente não existe
    assert response.status_code == 404, response.text

def test_update_meu_responsavel(client: TestClient):
    headers = get_operator_token(client, "op_resp_update")
    create_response = client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável para Atualizar",
            "cpf": generate_unique_cpf("008"),
            "email": generate_unique_email("resp_update"),
            "telefone_principal": "771234567",
        },
    )
    responsavel_id = create_response.json()["id_responsavel"]
    
    update_data = {"nome_completo": "Responsável ATUALIZADO com Sucesso"}
    response = client.put(f"/responsaveis/{responsavel_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_responsavel"] == responsavel_id
    assert data["nome_completo"] == "Responsável ATUALIZADO com Sucesso"

def test_delete_meu_responsavel(client: TestClient):
    headers = get_operator_token(client, "op_resp_delete")
    create_response = client.post(
        "/responsaveis",
        headers=headers,
        json={
            "nome_completo": "Responsável para Deletar",
            "cpf": generate_unique_cpf("009"),
            "email": generate_unique_email("resp_delete"),
            "telefone_principal": "881234567",
        },
    )
    responsavel_id = create_response.json()["id_responsavel"]
    
    response = client.delete(f"/responsaveis/{responsavel_id}", headers=headers)
    assert response.status_code == 200, response.text # O router retorna o objeto deletado com 200
    
    # Verifica se foi realmente deletado
    get_response = client.get(f"/responsaveis/{responsavel_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text

def test_responsavel_data_isolation(client: TestClient):
    # Operador A
    headers_op_a = get_operator_token(client, "opA_resp_iso")
    responsavel_op_a_data = {
        "nome_completo": "Responsável do Operador A",
        "cpf": generate_unique_cpf("100"),
        "email": generate_unique_email("resp_opA_iso"),
        "telefone_principal": "10101010",
    }
    create_resp_a = client.post("/responsaveis", headers=headers_op_a, json=responsavel_op_a_data)
    assert create_resp_a.status_code == 201
    id_responsavel_op_a = create_resp_a.json()["id_responsavel"]

    # Operador B
    headers_op_b = get_operator_token(client, "opB_resp_iso")

    # Operador B tenta ler o responsável do Operador A
    response_get = client.get(f"/responsaveis/{id_responsavel_op_a}", headers=headers_op_b)
    assert response_get.status_code == 404 # Não deve encontrar pois não pertence a ele

    # Operador B lista seus responsáveis (não deve ver o do Operador A)
    response_list = client.get("/responsaveis", headers=headers_op_b)
    assert response_list.status_code == 200
    responsaveis_op_b = response_list.json()
    assert not any(r["id_responsavel"] == id_responsavel_op_a for r in responsaveis_op_b)