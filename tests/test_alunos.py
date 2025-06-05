# tests/test_alunos.py
import pytest
from fastapi.testclient import TestClient
import datetime
from typing import Dict # Para type hinting
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# NOTA: Mova estas helpers para conftest.py em um projeto real!

def get_operator_token(client: TestClient, email_prefix: str) -> Dict[str, str]:
    """Registra um novo operador e retorna o cabeçalho de autorização com o token."""
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword_aluno"
    
    reg_payload = {"email": email, "password": password, "nome_completo": f"Operador {email_prefix} Alunos"}
    client.post("/users/register", json=reg_payload)
    
    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Falha ao obter token para {email} no helper de alunos: {login_response.text} (Payload registro: {reg_payload})")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_string(prefix: str = "test_alu_") -> str:
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

def create_test_escola_for_operator(client: TestClient, headers: Dict[str, str], nome_prefix: str = "EscAluno") -> schemas.Escola:
    nome_escola = f"{nome_prefix}_{generate_unique_string(str(datetime.datetime.now().microsecond))}"[:100]
    response = client.post(
        "/escolas", headers=headers, json={"nome_escola": nome_escola, "endereco_completo": f"Rua Escola para Aluno {nome_prefix}"}
    )
    if response.status_code != 201:
        pytest.fail(f"Helper: Falha ao criar escola de teste '{nome_escola}' para Aluno: {response.text}")
    return schemas.Escola(**response.json())

def create_test_responsavel_for_operator(client: TestClient, headers: Dict[str, str], cpf_prefix: str = "777A") -> schemas.Responsavel:
    cpf = f"{cpf_prefix}{generate_unique_string()[-7:]}"[-11:]
    email = f"resp_aluno_{cpf_prefix}{generate_unique_string()}@example.com"
    response = client.post(
        "/responsaveis", headers=headers, json={
            "nome_completo": f"Responsável Aluno {cpf_prefix}", "cpf": cpf,
            "email": email, "telefone_principal": "77778888"
        }
    )
    if response.status_code != 201:
        pytest.fail(f"Helper: Falha ao criar responsável de teste '{cpf}' para Aluno: {response.text}")
    return schemas.Responsavel(**response.json())

# Fixture para ter um operador com uma escola e um responsável criados
@pytest.fixture(scope="function")
def setup_operador_com_escola_e_responsavel(client: TestClient):
    headers = get_operator_token(client, "op_aluno_setup")
    escola = create_test_escola_for_operator(client, headers, "EscolaBaseAluno")
    responsavel = create_test_responsavel_for_operator(client, headers, "RespBaseAluno")
    return headers, escola, responsavel

# --- Testes para Alunos ---

def test_create_aluno_success(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers, escola, responsavel = setup_operador_com_escola_e_responsavel
    nome_aluno = generate_unique_string("Aluno Sucesso ")
    data_nascimento_aluno = (datetime.date.today() - datetime.timedelta(days=365*6)).isoformat() # 6 anos

    aluno_data = {
        "nome_completo_aluno": nome_aluno,
        "data_nascimento": data_nascimento_aluno,
        "id_responsavel_principal": responsavel.id_responsavel,
        "id_escola": escola.id_escola,
        "endereco_embarque_predeterminado": "Casa do Aluno Sucesso, 123",
        "periodo_escolar": "Manhã",
        "turma_serie": "1A"
    }
    response = client.post("/alunos", headers=headers, json=aluno_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nome_completo_aluno"] == nome_aluno
    assert data["id_escola"] == escola.id_escola
    assert data["id_responsavel_principal"] == responsavel.id_responsavel
    assert "id_aluno" in data

def test_create_aluno_unauthenticated(client: TestClient, setup_operador_com_escola_e_responsavel):
    _, escola, responsavel = setup_operador_com_escola_e_responsavel # Precisamos dos IDs
    aluno_data = {
        "nome_completo_aluno": "Aluno Sem Auth", "data_nascimento": "2017-01-01",
        "id_responsavel_principal": responsavel.id_responsavel, "id_escola": escola.id_escola,
        "endereco_embarque_predeterminado": "Rua Sem Auth", "periodo_escolar": "Tarde"
    }
    response = client.post("/alunos", json=aluno_data) # Sem headers
    assert response.status_code == 401, response.text

def test_create_aluno_escola_nao_pertence_ao_operador(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers_op_a, _, responsavel_op_a = setup_operador_com_escola_e_responsavel # Escola e Resp do Op A

    # Cria Operador B e sua própria escola
    headers_op_b = get_operator_token(client, "opB_aluno_esc_err")
    escola_op_b = create_test_escola_for_operator(client, headers_op_b, "EscolaDoOpB")
    # Responsável do Op A será usado incorretamente
    
    aluno_data = {
        "nome_completo_aluno": "Aluno Escola Errada", "data_nascimento": "2018-01-01",
        "id_responsavel_principal": responsavel_op_a.id_responsavel, # Responsável do Op A
        "id_escola": escola_op_b.id_escola, # Escola do Op B
        "endereco_embarque_predeterminado": "Rua Confusa", "periodo_escolar": "Integral"
    }
    # Operador A tenta criar aluno usando responsável dele mas escola do Operador B
    response = client.post("/alunos", headers=headers_op_a, json=aluno_data)
    assert response.status_code == 400, response.text
    assert "Escola fornecida é inválida ou não pertence a você" in response.json()["detail"]

def test_create_aluno_responsavel_nao_pertence_ao_operador(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers_op_a, escola_op_a, _ = setup_operador_com_escola_e_responsavel # Escola do Op A

    # Cria Operador B e seu próprio responsável
    headers_op_b = get_operator_token(client, "opB_aluno_resp_err")
    responsavel_op_b = create_test_responsavel_for_operator(client, headers_op_b, "RespDoOpB")
    
    aluno_data = {
        "nome_completo_aluno": "Aluno Resp Errado", "data_nascimento": "2019-01-01",
        "id_responsavel_principal": responsavel_op_b.id_responsavel, # Responsável do Op B
        "id_escola": escola_op_a.id_escola, # Escola do Op A
        "endereco_embarque_predeterminado": "Rua Mais Confusa", "periodo_escolar": "Manhã"
    }
    # Operador A tenta criar aluno usando escola dele mas responsável do Operador B
    response = client.post("/alunos", headers=headers_op_a, json=aluno_data)
    assert response.status_code == 400, response.text
    assert "Responsável principal fornecido é inválido ou não pertence a você" in response.json()["detail"]


def test_list_meus_alunos(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers, escola, responsavel = setup_operador_com_escola_e_responsavel
    nome_aluno_lista = generate_unique_string("Aluno Para Lista ")
    client.post("/alunos", headers=headers, json={
        "nome_completo_aluno": nome_aluno_lista, "data_nascimento": "2015-05-05",
        "id_responsavel_principal": responsavel.id_responsavel, "id_escola": escola.id_escola,
        "endereco_embarque_predeterminado": "End Aluno Lista", "periodo_escolar": "Tarde"
    })
    
    response = client.get("/alunos", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(a["nome_completo_aluno"] == nome_aluno_lista for a in data)

def test_get_meu_aluno_by_id_success(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers, escola, responsavel = setup_operador_com_escola_e_responsavel
    nome_aluno_get = generate_unique_string("Aluno para GET ID ")
    create_response = client.post("/alunos", headers=headers, json={
        "nome_completo_aluno": nome_aluno_get, "data_nascimento": "2016-06-06",
        "id_responsavel_principal": responsavel.id_responsavel, "id_escola": escola.id_escola,
        "endereco_embarque_predeterminado": "End Aluno GET ID", "periodo_escolar": "Manhã"
    })
    aluno_id = create_response.json()["id_aluno"]
    
    response = client.get(f"/alunos/{aluno_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_aluno"] == aluno_id
    assert data["nome_completo_aluno"] == nome_aluno_get

def test_get_aluno_nao_existente(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers, _, _ = setup_operador_com_escola_e_responsavel
    response = client.get("/alunos/9999999", headers=headers) # ID improvável
    assert response.status_code == 404, response.text

def test_update_meu_aluno_success(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers, escola, responsavel = setup_operador_com_escola_e_responsavel
    create_response = client.post("/alunos", headers=headers, json={
        "nome_completo_aluno": generate_unique_string("Aluno Original Update "), "data_nascimento": "2017-07-07",
        "id_responsavel_principal": responsavel.id_responsavel, "id_escola": escola.id_escola,
        "endereco_embarque_predeterminado": "End Aluno Original Update", "periodo_escolar": "Tarde"
    })
    aluno_id = create_response.json()["id_aluno"]
    
    novo_nome_aluno = generate_unique_string("Aluno ATUALIZADO ")
    update_data = {"nome_completo_aluno": novo_nome_aluno, "periodo_escolar": "Integral"}
    response = client.put(f"/alunos/{aluno_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_aluno"] == aluno_id
    assert data["nome_completo_aluno"] == novo_nome_aluno
    assert data["periodo_escolar"] == "Integral"

def test_delete_meu_aluno_success(client: TestClient, setup_operador_com_escola_e_responsavel):
    headers, escola, responsavel = setup_operador_com_escola_e_responsavel
    create_response = client.post("/alunos", headers=headers, json={
        "nome_completo_aluno": generate_unique_string("Aluno para Deletar "), "data_nascimento": "2018-08-08",
        "id_responsavel_principal": responsavel.id_responsavel, "id_escola": escola.id_escola,
        "endereco_embarque_predeterminado": "End Aluno Deletar", "periodo_escolar": "Manhã"
    })
    aluno_id = create_response.json()["id_aluno"]
    
    response = client.delete(f"/alunos/{aluno_id}", headers=headers)
    assert response.status_code == 200, response.text 
    
    get_response = client.get(f"/alunos/{aluno_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text

def test_aluno_data_isolation(client: TestClient):
    # Operador A cria escola, responsável e aluno
    headers_op_a = get_operator_token(client, "opA_aluno_iso")
    escola_op_a = create_test_escola_for_operator(client, headers_op_a, "EscAIso")
    responsavel_op_a = create_test_responsavel_for_operator(client, headers_op_a, "RespAIso")
    aluno_op_a_resp = client.post("/alunos", headers=headers_op_a, json={
        "nome_completo_aluno": "Aluno do Op A", "data_nascimento": "2019-09-09",
        "id_responsavel_principal": responsavel_op_a.id_responsavel, "id_escola": escola_op_a.id_escola,
        "endereco_embarque_predeterminado": "End Op A", "periodo_escolar": "Tarde"
    })
    assert aluno_op_a_resp.status_code == 201, aluno_op_a_resp.text
    id_aluno_op_a = aluno_op_a_resp.json()["id_aluno"]

    # Operador B
    headers_op_b = get_operator_token(client, "opB_aluno_iso")

    # 1. Operador B tenta LER o aluno do Operador A pelo ID
    response_get_b_for_a = client.get(f"/alunos/{id_aluno_op_a}", headers=headers_op_b)
    assert response_get_b_for_a.status_code == 404

    # 2. Operador B lista seus alunos (não deve ver o do Operador A)
    response_list_b = client.get("/alunos", headers=headers_op_b)
    assert response_list_b.status_code == 200
    alunos_op_b = response_list_b.json()
    assert not any(a["id_aluno"] == id_aluno_op_a for a in alunos_op_b)

    # 3. Operador B tenta ATUALIZAR o aluno do Operador A
    update_data_b_for_a = {"nome_completo_aluno": "Tentativa Update Aluno por B"}
    response_put_b_for_a = client.put(f"/alunos/{id_aluno_op_a}", headers=headers_op_b, json=update_data_b_for_a)
    assert response_put_b_for_a.status_code == 404 

    # 4. Operador B tenta DELETAR o aluno do Operador A
    response_delete_b_for_a = client.delete(f"/alunos/{id_aluno_op_a}", headers=headers_op_b)
    assert response_delete_b_for_a.status_code == 404