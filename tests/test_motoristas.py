# tests/test_motoristas.py
import pytest
from fastapi.testclient import TestClient
import datetime # Para gerar dados únicos e para datas
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# NOTA: Idealmente, a função get_operator_token e geradores de dados únicos
# estariam em conftest.py para serem reutilizados por todos os arquivos de teste.
# Vou incluí-la aqui para manter este exemplo autocontido por enquanto.

def get_operator_token(client: TestClient, email_prefix: str) -> dict:
    """Registra um novo operador e retorna o cabeçalho de autorização com o token."""
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword"
    
    reg_response = client.post(
        "/users/register",
        json={"email": email, "password": password, "nome_completo": f"Operador {email_prefix}"},
    )
    # Em um ambiente de teste limpo por função (com rollback), o usuário sempre será novo.
    # Se o registro falhar aqui, o teste deve falhar.
    if reg_response.status_code != 201:
         # Tenta logar se o usuário já existir (pode acontecer se o rollback não for perfeito entre módulos)
        pass 

    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Falha ao obter token para {email} durante o setup do teste: {login_response.text} (Registro status: {reg_response.status_code})")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_string(prefix: str = "test_") -> str:
    """Gera uma string pseudo-única para testes."""
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

# --- Testes para Motoristas ---

def test_create_motorista_success(client: TestClient):
    headers = get_operator_token(client, "op_motor_create")
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    
    motorista_data = {
        "nome_completo": "Motorista Asdrubal Teste",
        "cpf": generate_unique_string("111222333")[-11:], # Exemplo simples de CPF único
        "cnh_numero": generate_unique_string("CNH")[-9:],  # Exemplo CNH única
        "cnh_categoria": "D",
        "cnh_validade": cnh_validade_futura,
        "telefone": "47912345678",
        "email": generate_unique_string("motor_success") + "@example.com",
        "ativo": True
    }
    response = client.post("/motoristas", headers=headers, json=motorista_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nome_completo"] == motorista_data["nome_completo"]
    assert data["cpf"] == motorista_data["cpf"]
    assert data["cnh_numero"] == motorista_data["cnh_numero"]
    assert "id_motorista" in data

def test_create_motorista_unauthenticated(client: TestClient):
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    motorista_data = {
        "nome_completo": "Motorista Sem Auth",
        "cpf": generate_unique_string("222333444")[-11:],
        "cnh_numero": generate_unique_string("CNHNoAuth")[-9:],
        "cnh_categoria": "D",
        "cnh_validade": cnh_validade_futura,
        "telefone": "47988887777",
    }
    response = client.post("/motoristas", json=motorista_data)
    assert response.status_code == 401, response.text

def test_create_motorista_duplicate_cpf_for_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_motor_dupcpf")
    cpf_unico = generate_unique_string("333444555")[-11:]
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()

    client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista CPF Original", "cpf": cpf_unico,
            "cnh_numero": generate_unique_string("CNHOrigCPF")[-9:], "cnh_categoria": "D",
            "cnh_validade": cnh_validade_futura, "telefone": "111",
            "email": generate_unique_string("motor_cpf1") + "@example.com"
        }
    )
    response_duplicate = client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista CPF Duplicado", "cpf": cpf_unico, # Mesmo CPF
            "cnh_numero": generate_unique_string("CNHDupCPF")[-9:], "cnh_categoria": "D",
            "cnh_validade": cnh_validade_futura, "telefone": "222",
            "email": generate_unique_string("motor_cpf2") + "@example.com"
        }
    )
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui um motorista com o CPF" in response_duplicate.json()["detail"]

def test_create_motorista_duplicate_cnh_for_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_motor_dupcnh")
    cnh_unica = generate_unique_string("CNHDuplicada")[-9:]
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()

    client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista CNH Original", "cpf": generate_unique_string("444")[-11:],
            "cnh_numero": cnh_unica, "cnh_categoria": "D", "cnh_validade": cnh_validade_futura,
            "telefone": "333", "email": generate_unique_string("motor_cnh1") + "@example.com"
        }
    )
    response_duplicate = client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista CNH Duplicada", "cpf": generate_unique_string("555")[-11:],
            "cnh_numero": cnh_unica, "cnh_categoria": "D", "cnh_validade": cnh_validade_futura,
            "telefone": "444", "email": generate_unique_string("motor_cnh2") + "@example.com"
        }
    )
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui um motorista com a CNH" in response_duplicate.json()["detail"]


def test_list_meus_motoristas(client: TestClient):
    headers = get_operator_token(client, "op_motor_list")
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista para Listagem", "cpf": generate_unique_string("666")[-11:],
            "cnh_numero": generate_unique_string("CNHList")[-9:], "cnh_categoria": "D",
            "cnh_validade": cnh_validade_futura, "telefone": "555"
        }
    )
    response = client.get("/motoristas", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(m["nome_completo"] == "Motorista para Listagem" for m in data)

def test_get_meu_motorista_by_id(client: TestClient):
    headers = get_operator_token(client, "op_motor_getid")
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    create_response = client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista para GET ID", "cpf": generate_unique_string("777")[-11:],
            "cnh_numero": generate_unique_string("CNHGetID")[-9:], "cnh_categoria": "D",
            "cnh_validade": cnh_validade_futura, "telefone": "666"
        }
    )
    motorista_id = create_response.json()["id_motorista"]
    
    response = client.get(f"/motoristas/{motorista_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_motorista"] == motorista_id
    assert data["nome_completo"] == "Motorista para GET ID"

def test_update_meu_motorista(client: TestClient):
    headers = get_operator_token(client, "op_motor_update")
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    create_response = client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista para Atualizar", "cpf": generate_unique_string("888")[-11:],
            "cnh_numero": generate_unique_string("CNHUpdate")[-9:], "cnh_categoria": "D",
            "cnh_validade": cnh_validade_futura, "telefone": "777"
        }
    )
    motorista_id = create_response.json()["id_motorista"]
    
    update_data = {"nome_completo": "Motorista ATUALIZADO", "ativo": False}
    response = client.put(f"/motoristas/{motorista_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_motorista"] == motorista_id
    assert data["nome_completo"] == "Motorista ATUALIZADO"
    assert data["ativo"] == False

def test_delete_meu_motorista(client: TestClient):
    headers = get_operator_token(client, "op_motor_delete")
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    create_response = client.post(
        "/motoristas", headers=headers, json={
            "nome_completo": "Motorista para Deletar", "cpf": generate_unique_string("999")[-11:],
            "cnh_numero": generate_unique_string("CNHDelete")[-9:], "cnh_categoria": "D",
            "cnh_validade": cnh_validade_futura, "telefone": "888"
        }
    )
    motorista_id = create_response.json()["id_motorista"]
    
    response = client.delete(f"/motoristas/{motorista_id}", headers=headers)
    assert response.status_code == 200, response.text 
    
    get_response = client.get(f"/motoristas/{motorista_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text

def test_motorista_data_isolation(client: TestClient):
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    # Operador A
    headers_op_a = get_operator_token(client, "opA_motor_iso")
    motorista_op_a_data = {
        "nome_completo": "Motorista do Operador A", "cpf": generate_unique_string("101")[-11:],
        "cnh_numero": generate_unique_string("CNHisoA")[-9:], "cnh_categoria": "D",
        "cnh_validade": cnh_validade_futura, "telefone": "1010",
        "email": generate_unique_string("motor_isoA") + "@example.com"
    }
    create_resp_a = client.post("/motoristas", headers=headers_op_a, json=motorista_op_a_data)
    assert create_resp_a.status_code == 201
    id_motorista_op_a = create_resp_a.json()["id_motorista"]

    # Operador B
    headers_op_b = get_operator_token(client, "opB_motor_iso")

    # Operador B tenta ler o motorista do Operador A
    response_get = client.get(f"/motoristas/{id_motorista_op_a}", headers=headers_op_b)
    assert response_get.status_code == 404 

    # Operador B lista seus motoristas (não deve ver o do Operador A)
    response_list = client.get("/motoristas", headers=headers_op_b)
    assert response_list.status_code == 200
    motoristas_op_b = response_list.json()
    assert not any(m["id_motorista"] == id_motorista_op_a for m in motoristas_op_b)