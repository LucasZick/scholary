# tests/test_vans.py
import pytest
from fastapi.testclient import TestClient
import datetime
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# NOTA: Idealmente, estas funções helper estariam em conftest.py.
# Vou incluí-las aqui para manter o exemplo autocontido.

def get_operator_token(client: TestClient, email_prefix: str) -> dict:
    """Registra um novo operador e retorna o cabeçalho de autorização com o token."""
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword"
    
    client.post(
        "/users/register",
        json={"email": email, "password": password, "nome_completo": f"Operador {email_prefix}"},
    )
    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Falha ao obter token para {email}: {login_response.text}")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_placa(prefix: str = "VAN") -> str:
    """Gera uma placa pseudo-única para testes."""
    # Formato simples, ajuste se precisar de um formato de placa real (ex: ABC1D23)
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')[-4:]}"

def create_test_motorista_for_operator(client: TestClient, headers: dict, cpf_prefix: str = "111") -> schemas.Motorista:
    """Cria um motorista para o operador logado e retorna o objeto Motorista."""
    cnh_validade_futura = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    motorista_data = {
        "nome_completo": f"Motorista Helper {cpf_prefix}",
        "cpf": f"{cpf_prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')[-8:]}"[-11:],
        "cnh_numero": f"CNH{cpf_prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')[-5:]}"[-9:],
        "cnh_categoria": "D",
        "cnh_validade": cnh_validade_futura,
        "telefone": "999999999",
        "email": f"motorista_helper_{cpf_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com",
    }
    response = client.post("/motoristas", headers=headers, json=motorista_data)
    if response.status_code != 201:
        pytest.fail(f"Falha ao criar motorista de teste: {response.text}")
    return schemas.Motorista(**response.json())

# --- Testes para Vans ---

def test_create_van_success_sem_motorista(client: TestClient):
    headers = get_operator_token(client, "op_van_create_sm")
    van_data = {
        "placa": generate_unique_placa("TSM"), # Teste Sem Motorista
        "modelo_veiculo": "Sprinter",
        "marca_veiculo": "Mercedes",
        "ano_fabricacao": 2022,
        "capacidade_passageiros": 15,
    }
    response = client.post("/vans", headers=headers, json=van_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["placa"] == van_data["placa"]
    assert data["modelo_veiculo"] == van_data["modelo_veiculo"]
    assert "id_van" in data
    assert data["id_motorista_padrao"] is None

def test_create_van_success_com_motorista(client: TestClient):
    headers = get_operator_token(client, "op_van_create_cm")
    motorista = create_test_motorista_for_operator(client, headers, "121")
    
    van_data = {
        "placa": generate_unique_placa("TCM"), # Teste Com Motorista
        "modelo_veiculo": "Ducato",
        "marca_veiculo": "Fiat",
        "ano_fabricacao": 2023,
        "capacidade_passageiros": 12,
        "id_motorista_padrao": motorista.id_motorista
    }
    response = client.post("/vans", headers=headers, json=van_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["placa"] == van_data["placa"]
    assert data["id_motorista_padrao"] == motorista.id_motorista

def test_create_van_unauthenticated(client: TestClient):
    van_data = {"placa": generate_unique_placa("TUA"), "modelo_veiculo": "Transit", "marca_veiculo": "Ford", "ano_fabricacao": 2021, "capacidade_passageiros": 10}
    response = client.post("/vans", json=van_data)
    assert response.status_code == 401, response.text

def test_create_van_duplicate_placa_same_owner(client: TestClient):
    headers = get_operator_token(client, "op_van_dupplaca")
    placa_unica = generate_unique_placa("DUP")
    
    client.post("/vans", headers=headers, json={
        "placa": placa_unica, "modelo_veiculo": "Modelo A", "marca_veiculo": "Marca X",
        "ano_fabricacao": 2020, "capacidade_passageiros": 10
    })
    response_duplicate = client.post("/vans", headers=headers, json={
        "placa": placa_unica, "modelo_veiculo": "Modelo B", "marca_veiculo": "Marca Y",
        "ano_fabricacao": 2021, "capacidade_passageiros": 12
    })
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Você já possui uma van com a placa" in response_duplicate.json()["detail"]

def test_create_van_invalid_motorista_id(client: TestClient):
    headers = get_operator_token(client, "op_van_invmotor")
    van_data = {
        "placa": generate_unique_placa("TIM"), # Teste Inv Motorista
        "modelo_veiculo": "Master", "marca_veiculo": "Renault",
        "ano_fabricacao": 2022, "capacidade_passageiros": 16,
        "id_motorista_padrao": 999999 # ID de motorista que provavelmente não existe
    }
    response = client.post("/vans", headers=headers, json=van_data)
    assert response.status_code == 400, response.text # Esperando erro do router/CRUD
    assert "Motorista padrão fornecido é inválido" in response.json()["detail"]


def test_list_minhas_vans(client: TestClient):
    headers = get_operator_token(client, "op_van_list")
    client.post("/vans", headers=headers, json={
        "placa": generate_unique_placa("TLV"), "modelo_veiculo": "Van de Lista", 
        "marca_veiculo": "Marca L", "ano_fabricacao": 2020, "capacidade_passageiros": 8
    })
    response = client.get("/vans", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(v["placa"].startswith("TLV") for v in data)


def test_get_minha_van_by_id(client: TestClient):
    headers = get_operator_token(client, "op_van_getid")
    create_response = client.post(
        "/vans", headers=headers, json={
            "placa": generate_unique_placa("TGV"), "modelo_veiculo": "Van para GET", 
            "marca_veiculo": "Marca G", "ano_fabricacao": 2021, "capacidade_passageiros": 10
        }
    )
    van_id = create_response.json()["id_van"]
    
    response = client.get(f"/vans/{van_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_van"] == van_id
    assert data["placa"].startswith("TGV")

def test_update_minha_van(client: TestClient):
    headers = get_operator_token(client, "op_van_update")
    motorista1 = create_test_motorista_for_operator(client, headers, "122")
    motorista2 = create_test_motorista_for_operator(client, headers, "123")

    create_response = client.post(
        "/vans", headers=headers, json={
            "placa": generate_unique_placa("TUV"), "modelo_veiculo": "Van para Update", 
            "marca_veiculo": "Marca U", "ano_fabricacao": 2022, "capacidade_passageiros": 12,
            "id_motorista_padrao": motorista1.id_motorista
        }
    )
    van_id = create_response.json()["id_van"]
    
    update_data = {"modelo_veiculo": "Van ATUALIZADA", "id_motorista_padrao": motorista2.id_motorista}
    response = client.put(f"/vans/{van_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_van"] == van_id
    assert data["modelo_veiculo"] == "Van ATUALIZADA"
    assert data["id_motorista_padrao"] == motorista2.id_motorista

def test_delete_minha_van(client: TestClient):
    headers = get_operator_token(client, "op_van_delete")
    create_response = client.post(
        "/vans", headers=headers, json={
            "placa": generate_unique_placa("TDV"), "modelo_veiculo": "Van para Deletar", 
            "marca_veiculo": "Marca D", "ano_fabricacao": 2023, "capacidade_passageiros": 14
        }
    )
    van_id = create_response.json()["id_van"]
    
    response = client.delete(f"/vans/{van_id}", headers=headers)
    assert response.status_code == 200, response.text 
    
    get_response = client.get(f"/vans/{van_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text

def test_van_data_isolation(client: TestClient):
    # Operador A
    headers_op_a = get_operator_token(client, "opA_van_iso")
    van_op_a_data = {
        "placa": generate_unique_placa("VOA"), "modelo_veiculo": "Van do Op A", 
        "marca_veiculo": "Marca A", "ano_fabricacao": 2020, "capacidade_passageiros": 10
    }
    create_resp_a = client.post("/vans", headers=headers_op_a, json=van_op_a_data)
    assert create_resp_a.status_code == 201
    id_van_op_a = create_resp_a.json()["id_van"]

    # Operador B
    headers_op_b = get_operator_token(client, "opB_van_iso")

    # Operador B tenta ler a van do Operador A
    response_get = client.get(f"/vans/{id_van_op_a}", headers=headers_op_b)
    assert response_get.status_code == 404 

    # Operador B lista suas vans (não deve ver a do Operador A)
    response_list = client.get("/vans", headers=headers_op_b)
    assert response_list.status_code == 200
    vans_op_b = response_list.json()
    assert not any(v["id_van"] == id_van_op_a for v in vans_op_b)