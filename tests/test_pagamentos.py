# tests/test_pagamentos.py
import pytest
from fastapi.testclient import TestClient
import datetime
from decimal import Decimal
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# NOTA: Estas funções helper estão se repetindo. Em um projeto maior,
# elas seriam centralizadas em conftest.py e passadas como fixtures.
# Incluindo-as aqui para manter o exemplo autocontido.

def get_operator_token(client: TestClient, email_prefix: str) -> dict:
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

def generate_unique_string(prefix: str = "test_") -> str:
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

# --- Helpers para criar entidades pré-requisito ---
def create_test_escola_for_operator(client: TestClient, headers: dict, nome_prefix: str = "EscPag") -> schemas.Escola:
    nome_escola = f"{nome_prefix}_{generate_unique_string()}"[-100:]
    response = client.post("/escolas", headers=headers, json={"nome_escola": nome_escola, "endereco_completo": "Rua Escola Pag"})
    if response.status_code != 201: pytest.fail(f"Falha ao criar escola teste: {response.text}")
    return schemas.Escola(**response.json())

def create_test_responsavel_for_operator(client: TestClient, headers: dict, cpf_prefix: str = "333") -> schemas.Responsavel:
    cpf = f"{cpf_prefix}{generate_unique_string()[-8:]}"[-11:]
    email = f"resp_pag_{generate_unique_string()}@example.com"
    response = client.post("/responsaveis", headers=headers, json={"nome_completo": f"Resp Pag {cpf_prefix}", "cpf": cpf, "email": email, "telefone_principal": "33334444"})
    if response.status_code != 201: pytest.fail(f"Falha ao criar responsável teste: {response.text}")
    return schemas.Responsavel(**response.json())

def create_test_aluno_for_operator(client: TestClient, headers: dict, escola_id: int, responsavel_id: int, nome_prefix: str = "AlunoPag") -> schemas.Aluno:
    nome_aluno = f"{nome_prefix}_{generate_unique_string()}"[-100:]
    data_nascimento = (datetime.date.today() - datetime.timedelta(days=365*8)).isoformat() # Aluno com 8 anos
    response = client.post("/alunos", headers=headers, json={
        "nome_completo_aluno": nome_aluno, "data_nascimento": data_nascimento,
        "id_responsavel_principal": responsavel_id, "id_escola": escola_id,
        "endereco_embarque_predeterminado": "Casa Aluno Pag", "periodo_escolar": "Tarde"
    })
    if response.status_code != 201: pytest.fail(f"Falha ao criar aluno teste: {response.text}")
    return schemas.Aluno(**response.json())

def create_test_contrato_for_operator(client: TestClient, headers: dict, aluno_id: int, responsavel_id: int) -> schemas.ContratoServico:
    data_inicio = datetime.date.today().isoformat()
    response = client.post("/contratos", headers=headers, json={
        "id_aluno": aluno_id, "id_responsavel_financeiro": responsavel_id,
        "data_inicio_contrato": data_inicio, "valor_mensal": "300.50",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Contrato para Pagamento"
    })
    if response.status_code != 201: pytest.fail(f"Falha ao criar contrato teste: {response.text}")
    return schemas.ContratoServico(**response.json())

# --- Testes para Pagamentos ---

@pytest.fixture(scope="function")
def setup_contrato(client: TestClient):
    """Fixture para criar um operador, suas entidades e um contrato, retornando headers e o contrato."""
    headers = get_operator_token(client, "op_pag")
    escola = create_test_escola_for_operator(client, headers)
    responsavel = create_test_responsavel_for_operator(client, headers)
    aluno = create_test_aluno_for_operator(client, headers, escola.id_escola, responsavel.id_responsavel)
    contrato = create_test_contrato_for_operator(client, headers, aluno.id_aluno, responsavel.id_responsavel)
    return headers, contrato

def test_create_pagamento_success(client: TestClient, setup_contrato):
    headers, contrato = setup_contrato
    data_vencimento = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
    
    pagamento_data = {
        "id_contrato": contrato.id_contrato,
        "mes_referencia": datetime.date.today().strftime("%Y-%m"), # Ex: "2025-05"
        "data_vencimento": data_vencimento,
        "valor_nominal": str(contrato.valor_mensal), # Enviar como string, Pydantic/Decimal cuidam
    }
    response = client.post("/pagamentos", headers=headers, json=pagamento_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id_contrato"] == contrato.id_contrato
    assert Decimal(data["valor_nominal"]) == contrato.valor_mensal
    assert data["status_pagamento"] == "Pendente"
    assert "id_pagamento" in data

def test_create_pagamento_unauthenticated(client: TestClient, setup_contrato):
    _, contrato = setup_contrato # Precisamos de um id_contrato válido, mesmo que o teste falhe na auth
    pagamento_data = {
        "id_contrato": contrato.id_contrato, "mes_referencia": "2025-06",
        "data_vencimento": "2025-06-05", "valor_nominal": "100.00"
    }
    response = client.post("/pagamentos", json=pagamento_data)
    assert response.status_code == 401, response.text

def test_create_pagamento_contrato_invalido(client: TestClient, setup_contrato):
    headers, _ = setup_contrato
    pagamento_data = {
        "id_contrato": 999999, # ID de contrato que não existe ou não pertence ao operador
        "mes_referencia": "2025-07",
        "data_vencimento": "2025-07-05",
        "valor_nominal": "120.00"
    }
    response = client.post("/pagamentos", headers=headers, json=pagamento_data)
    assert response.status_code == 400, response.text # Ou 404 dependendo do tratamento no router
    assert "Contrato fornecido é inválido" in response.json()["detail"]

def test_list_pagamentos_por_contrato(client: TestClient, setup_contrato):
    headers, contrato = setup_contrato
    # Cria um pagamento para o contrato
    client.post("/pagamentos", headers=headers, json={
        "id_contrato": contrato.id_contrato, "mes_referencia": "2025-08",
        "data_vencimento": "2025-08-05", "valor_nominal": str(contrato.valor_mensal)
    })

    response = client.get(f"/pagamentos/por-contrato/{contrato.id_contrato}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id_contrato"] == contrato.id_contrato

def test_get_meu_pagamento_by_id(client: TestClient, setup_contrato):
    headers, contrato = setup_contrato
    create_pag_response = client.post("/pagamentos", headers=headers, json={
        "id_contrato": contrato.id_contrato, "mes_referencia": "2025-09",
        "data_vencimento": "2025-09-05", "valor_nominal": str(contrato.valor_mensal)
    })
    pagamento_id = create_pag_response.json()["id_pagamento"]

    response = client.get(f"/pagamentos/{pagamento_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_pagamento"] == pagamento_id
    assert Decimal(data["valor_nominal"]) == contrato.valor_mensal

def test_update_meu_pagamento_marcar_como_pago(client: TestClient, setup_contrato):
    headers, contrato = setup_contrato
    data_vencimento = datetime.date.today().isoformat()
    create_pag_response = client.post("/pagamentos", headers=headers, json={
        "id_contrato": contrato.id_contrato, "mes_referencia": datetime.date.today().strftime("%Y-%m"),
        "data_vencimento": data_vencimento, "valor_nominal": "200.00"
    })
    pagamento_id = create_pag_response.json()["id_pagamento"]

    update_data = {
        "status_pagamento": "Pago",
        "valor_pago": "200.00",
        "data_pagamento": datetime.date.today().isoformat(),
        "metodo_pagamento": "PIX"
    }
    response = client.put(f"/pagamentos/{pagamento_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status_pagamento"] == "Pago"
    assert Decimal(data["valor_pago"]) == Decimal("200.00")
    assert data["data_pagamento"] == datetime.date.today().isoformat()

def test_delete_meu_pagamento(client: TestClient, setup_contrato):
    headers, contrato = setup_contrato
    create_pag_response = client.post("/pagamentos", headers=headers, json={
        "id_contrato": contrato.id_contrato, "mes_referencia": "2025-10",
        "data_vencimento": "2025-10-05", "valor_nominal": "50.00"
    })
    pagamento_id = create_pag_response.json()["id_pagamento"]

    response = client.delete(f"/pagamentos/{pagamento_id}", headers=headers)
    assert response.status_code == 200, response.text # Ou 204 se não retornar conteúdo
    
    get_response = client.get(f"/pagamentos/{pagamento_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text

def test_pagamento_data_isolation(client: TestClient, setup_contrato):
    headers_op_a, contrato_op_a = setup_contrato # Operador A e seu contrato
    
    # Operador A cria um pagamento
    pagamento_op_a_resp = client.post("/pagamentos", headers=headers_op_a, json={
        "id_contrato": contrato_op_a.id_contrato, "mes_referencia": "2025-11",
        "data_vencimento": "2025-11-05", "valor_nominal": "10.00"
    })
    assert pagamento_op_a_resp.status_code == 201
    id_pagamento_op_a = pagamento_op_a_resp.json()["id_pagamento"]

    # Operador B
    headers_op_b = get_operator_token(client, "opB_pag_iso")
    # (Opcional: Operador B cria suas próprias entidades se necessário para o teste, mas não para este cenário)

    # Operador B tenta ler o pagamento do Operador A
    response_get = client.get(f"/pagamentos/{id_pagamento_op_a}", headers=headers_op_b)
    assert response_get.status_code == 404 # Não deve encontrar

    # Operador B tenta listar pagamentos do contrato do Operador A
    response_list_contrato_a = client.get(f"/pagamentos/por-contrato/{contrato_op_a.id_contrato}", headers=headers_op_b)
    # O CRUD de pagamentos/por-contrato primeiro verifica se o contrato pertence ao usuário.
    # Se não pertence, ele retorna uma string de erro que o router converte para 404.
    assert response_list_contrato_a.status_code == 404
    assert "Contrato não encontrado ou não pertence a você" in response_list_contrato_a.json()["detail"]