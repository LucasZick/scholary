# tests/test_contratos_servico.py
import pytest
from fastapi.testclient import TestClient
import datetime
from decimal import Decimal
from typing import Dict, List, Tuple # Adicionado Tuple
import schemas # Seus Pydantic schemas

# --- Funções Helper (Mova para conftest.py em um projeto real) ---
def get_operator_token(client: TestClient, email_prefix: str) -> Dict[str, str]:
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword_contrato"
    client.post("/users/register", json={"email": email, "password": password, "nome_completo": f"Operador {email_prefix}"})
    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Helper: Falha ao obter token para {email}: {login_response.text}")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_string(prefix: str = "test_cs_") -> str:
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

def generate_unique_cnpj(prefix: str = "213234340001") -> str: # Ajustado para ser diferente do de escolas
    suffix = str(datetime.datetime.now().timestamp()).replace('.', '')[-2:]
    return f"{prefix}{suffix}"[-18:]

def create_test_escola_for_operator(client: TestClient, headers: Dict[str, str], nome_prefix: str = "EscContr") -> schemas.Escola:
    nome_escola = f"{nome_prefix}_{generate_unique_string(str(datetime.datetime.now().microsecond))}"[:100]
    cnpj_escola = generate_unique_cnpj(f"{datetime.datetime.now().microsecond}") # CNPJ único
    response = client.post(
        "/escolas", headers=headers, json={
            "nome_escola": nome_escola, 
            "endereco_completo": f"Rua Escola Contrato {nome_prefix}",
            "cnpj": cnpj_escola
            }
    )
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar escola '{nome_escola}': {response.text}")
    return schemas.Escola(**response.json())

def create_test_responsavel_for_operator(client: TestClient, headers: Dict[str, str], cpf_prefix: str = "333CS") -> schemas.Responsavel:
    cpf = f"{cpf_prefix}{generate_unique_string()[-7:]}"[-11:]
    email = f"resp_contrato_{cpf_prefix}{generate_unique_string()}@example.com"
    response = client.post(
        "/responsaveis", headers=headers, json={
            "nome_completo": f"Resp Contrato {cpf_prefix}", "cpf": cpf,
            "email": email, "telefone_principal": "33334444"
        }
    )
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar responsável '{cpf}': {response.text}")
    return schemas.Responsavel(**response.json())

def create_test_aluno_for_operator(
    client: TestClient, headers: Dict[str, str], escola_id: int, responsavel_id: int, nome_prefix: str = "AlunoContr"
) -> schemas.Aluno:
    nome_aluno = f"{nome_prefix}_{generate_unique_string()}"[:100]
    data_nascimento = (datetime.date.today() - datetime.timedelta(days=365*7)).isoformat() # Aluno com 7 anos
    response = client.post(
        "/alunos", headers=headers, json={
            "nome_completo_aluno": nome_aluno, "data_nascimento": data_nascimento,
            "id_responsavel_principal": responsavel_id, "id_escola": escola_id,
            "endereco_embarque_predeterminado": f"Casa {nome_aluno}", "periodo_escolar": "Manhã"
        }
    )
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar aluno '{nome_aluno}': {response.text}")
    return schemas.Aluno(**response.json())

# Helper proximo_mes (usado nos novos testes)
def proximo_mes(ano: int, mes: int) -> Tuple[int, int]: # Importar Tuple de typing
    mes += 1
    if mes > 12:
        mes = 1
        ano += 1
    return ano, mes


# Fixture para setup básico de entidades necessárias para um contrato
@pytest.fixture(scope="function")
def setup_pre_requisitos_contrato(client: TestClient):
    headers = get_operator_token(client, "op_contrato_prereq")
    escola = create_test_escola_for_operator(client, headers, "EscPreContr")
    responsavel = create_test_responsavel_for_operator(client, headers, "RespPreContr")
    aluno = create_test_aluno_for_operator(client, headers, escola.id_escola, responsavel.id_responsavel, "AlunoPreContr")
    return headers, aluno, responsavel, escola # Retorna 4 itens

# --- Testes para ContratoServico ---

def test_create_contrato_com_data_fim_gera_pagamentos(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato # O _ ignora a escola aqui
    
    data_inicio = datetime.date(2025, 1, 15)
    data_fim = datetime.date(2025, 3, 10)
    valor_mensal_contrato = Decimal("150.50")
    dia_vencimento = 5

    contrato_data = {
        "id_aluno": aluno.id_aluno,
        "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(),
        "data_fim_contrato": data_fim.isoformat(),
        "valor_mensal": str(valor_mensal_contrato),
        "dia_vencimento_mensalidade": dia_vencimento,
        "tipo_servico_contratado": "Janeiro a Março",
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 201, response.text
    contrato_criado = schemas.ContratoServico(**response.json())

    pagamentos_response = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert pagamentos_response.status_code == 200, pagamentos_response.text
    pagamentos_gerados = [schemas.Pagamento(**p) for p in pagamentos_response.json()]
    
    assert len(pagamentos_gerados) == 3

    pag_jan = next((p for p in pagamentos_gerados if p.mes_referencia == "2025-01"), None)
    assert pag_jan is not None
    assert pag_jan.data_vencimento == datetime.date(2025, 1, dia_vencimento)
    assert pag_jan.valor_nominal == valor_mensal_contrato
    assert pag_jan.status_pagamento == "Pendente" or "Atrasado" # Ou Atrasado se date.today() for > 2025-01-05

    pag_mar = next((p for p in pagamentos_gerados if p.mes_referencia == "2025-03"), None)
    assert pag_mar is not None
    assert pag_mar.data_vencimento == datetime.date(2025, 3, dia_vencimento)

def test_create_contrato_sem_data_fim_gera_pagamentos_ate_fim_ano(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    ano_corrente_teste = 2025 # Para consistência do teste
    data_inicio = datetime.date(ano_corrente_teste, 10, 5) 
    valor_mensal_contrato = Decimal("200.00")
    dia_vencimento = 15

    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": None,
        "valor_mensal": str(valor_mensal_contrato), "dia_vencimento_mensalidade": dia_vencimento,
        "tipo_servico_contratado": f"Até Fim do Ano {ano_corrente_teste}",
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 201, response.text
    contrato_criado = schemas.ContratoServico(**response.json())

    pagamentos_response = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert pagamentos_response.status_code == 200, pagamentos_response.text
    pagamentos_gerados = [schemas.Pagamento(**p) for p in pagamentos_response.json()]
    
    assert len(pagamentos_gerados) == 3 # Out, Nov, Dez de 2025

    pag_dez = next((p for p in pagamentos_gerados if p.mes_referencia == f"{ano_corrente_teste}-12"), None)
    assert pag_dez is not None
    assert pag_dez.data_vencimento == datetime.date(ano_corrente_teste, 12, dia_vencimento)

def test_delete_contrato_deleta_pagamentos_associados(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date(2025, 1, 1).isoformat(),
        "data_fim_contrato": datetime.date(2025, 2, 28).isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 10,
        "tipo_servico_contratado": "Para Deletar com Pagamentos"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    id_contrato_deletado = create_response.json()["id_contrato"]

    pagamentos_antes_delete_resp = client.get(f"/pagamentos/por-contrato/{id_contrato_deletado}", headers=headers)
    assert pagamentos_antes_delete_resp.status_code == 200
    assert len(pagamentos_antes_delete_resp.json()) == 2

    delete_response = client.delete(f"/contratos/{id_contrato_deletado}", headers=headers)
    assert delete_response.status_code == 200, delete_response.text

    get_contrato_response = client.get(f"/contratos/{id_contrato_deletado}", headers=headers)
    assert get_contrato_response.status_code == 404, get_contrato_response.text

    pagamentos_apos_delete_resp = client.get(f"/pagamentos/por-contrato/{id_contrato_deletado}", headers=headers)
    assert pagamentos_apos_delete_resp.status_code == 404 # Porque o contrato não existe mais para o user
    assert "Contrato não encontrado ou não pertence a você" in pagamentos_apos_delete_resp.json()["detail"]


def test_create_contrato_unauthenticated(client: TestClient, setup_pre_requisitos_contrato):
    _, aluno, responsavel, _ = setup_pre_requisitos_contrato
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": "2025-01-01", "valor_mensal": "100.00",
        "dia_vencimento_mensalidade": 5, "tipo_servico_contratado": "Teste Sem Auth"
    }
    response = client.post("/contratos", json=contrato_data)
    assert response.status_code == 401, response.text

def test_create_contrato_aluno_invalido(client: TestClient, setup_pre_requisitos_contrato):
    headers, _, responsavel, _ = setup_pre_requisitos_contrato
    contrato_data = {
        "id_aluno": 99999, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "150.00",
        "dia_vencimento_mensalidade": 5, "tipo_servico_contratado": "Teste Aluno Inválido"
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 400, response.text
    assert "Aluno fornecido é inválido" in response.json()["detail"]

def test_create_contrato_responsavel_invalido(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, _, _ = setup_pre_requisitos_contrato
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": 99999,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "180.00",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Teste Responsável Inválido"
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 400, response.text
    assert "Responsável financeiro fornecido é inválido" in response.json()["detail"]

def test_create_contrato_data_fim_anterior_a_inicio(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    data_inicio = datetime.date(2025, 5, 1)
    data_fim_invalida = datetime.date(2025, 4, 1)
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim_invalida.isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Data Fim Inválida"
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 400, response.text
    assert "Data final do contrato não pode ser anterior à data inicial" in response.json()["detail"]

def test_create_contrato_valor_mensal_invalido(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "0.00",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Valor Inválido"
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 422, response.text

def test_create_contrato_dia_vencimento_invalido(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "100.00",
        "dia_vencimento_mensalidade": 32, "tipo_servico_contratado": "Dia Vencimento Inválido"
    }
    response = client.post("/contratos", headers=headers, json=contrato_data)
    assert response.status_code == 422, response.text

def test_list_meus_contratos_com_itens(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    client.post("/contratos", headers=headers, json={
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "280.00",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Contrato para Lista com Itens"
    })
    response = client.get("/contratos", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["tipo_servico_contratado"] == "Contrato para Lista com Itens" for c in data)

# Testes para GET por ID, PUT e DELETE (já estavam na sua versão anterior de test_contratos_servico.py)
# Certifique-se de que eles usam a fixture setup_pre_requisitos_contrato corretamente.
# Exemplo para GET por ID:
def test_get_meu_contrato_por_id(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    create_resp = client.post("/contratos", headers=headers, json={
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "280.00",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Contrato para GET"
    })
    contrato_id = create_resp.json()["id_contrato"]

    response = client.get(f"/contratos/{contrato_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id_contrato"] == contrato_id

def test_update_meu_contrato_status_e_valor(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    create_resp = client.post("/contratos", headers=headers, json={
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), 
        "data_fim_contrato": (datetime.date.today() + datetime.timedelta(days=90)).isoformat(),
        "valor_mensal": "280.00",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Contrato para Update"
    })
    contrato_id = create_resp.json()["id_contrato"]

    update_payload = {"status_contrato": "Inativo", "valor_mensal": "290.50"}
    response = client.put(f"/contratos/{contrato_id}", headers=headers, json=update_payload)
    assert response.status_code == 200, response.text
    updated_data = response.json()
    assert updated_data["status_contrato"] == "Inativo"
    assert Decimal(updated_data["valor_mensal"]) == Decimal("290.50")

    # Verifica se os pagamentos pendentes foram afetados (se valor_mensal mudou)
    # ou cancelados (se status_contrato mudou para Cancelado/Suspenso)
    # A lógica de atualização de pagamentos que implementamos deve ter sido acionada.
    pagamentos_response = client.get(f"/pagamentos/por-contrato/{contrato_id}", headers=headers)
    assert pagamentos_response.status_code == 200
    pagamentos_atualizados = [schemas.Pagamento(**p) for p in pagamentos_response.json()]
    for pag in pagamentos_atualizados:
        if pag.status_pagamento not in ["Pago", "Cancelado"]: # Verifica apenas os não pagos/não cancelados
            assert pag.valor_nominal == Decimal("290.50")


def test_update_contrato_dia_vencimento_afeta_pagamentos_pendentes(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    data_inicio = datetime.date.today()
    if data_inicio.month > 10: 
        data_inicio = datetime.date(data_inicio.year + 1, 1, 1)
    else: 
        prox_ano_calc, prox_mes_calc = proximo_mes(data_inicio.year, data_inicio.month)
        data_inicio = datetime.date(prox_ano_calc, prox_mes_calc, 1)

    # Ajusta data_fim para ser um dia específico do mês para consistência
    mes_fim_calc = data_inicio.month + 2
    ano_fim_calc = data_inicio.year
    if mes_fim_calc > 12:
        ano_fim_calc += (mes_fim_calc -1) // 12
        mes_fim_calc = (mes_fim_calc -1) % 12 + 1
    data_fim = datetime.date(ano_fim_calc, mes_fim_calc, 15)


    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(),
        "data_fim_contrato": data_fim.isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 10,
        "tipo_servico_contratado": "Teste Dia Vencimento"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201, create_response.text
    contrato_criado = schemas.ContratoServico(**create_response.json())
    
    update_payload = {"dia_vencimento_mensalidade": 20}
    update_response = client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload)
    assert update_response.status_code == 200, update_response.text

    pagamentos_response = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert pagamentos_response.status_code == 200
    pagamentos_atualizados = [schemas.Pagamento(**p) for p in pagamentos_response.json()]

    assert len(pagamentos_atualizados) > 0
    for pag in pagamentos_atualizados:
        if pag.status_pagamento not in ["Pago", "Cancelado"]: # Só checa pendentes/atrasados
            assert pag.data_vencimento.day == 20
            mes_referencia_pag = int(pag.mes_referencia.split('-')[1])
            ano_referencia_pag = int(pag.mes_referencia.split('-')[0])
            assert pag.data_vencimento.month == mes_referencia_pag
            assert pag.data_vencimento.year == ano_referencia_pag
            # Reavalia status baseado na nova data de vencimento e hoje
            if pag.data_vencimento < datetime.date.today():
                assert pag.status_pagamento == "Atrasado"
            else:
                assert pag.status_pagamento == "Pendente"


def test_update_contrato_dia_vencimento_para_dia_invalido_em_mes_curto(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    data_inicio = datetime.date(2025, 1, 1) 
    data_fim = datetime.date(2025, 3, 31)
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim.isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 10,
        "tipo_servico_contratado": "Teste Dia Inválido Fev"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    contrato_criado = schemas.ContratoServico(**create_response.json())

    update_payload = {"dia_vencimento_mensalidade": 30} # Inválido para Fev
    client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload)
    
    pagamentos_response = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert pagamentos_response.status_code == 200
    pagamentos_atualizados = [schemas.Pagamento(**p) for p in pagamentos_response.json()]

    pagamento_fevereiro = next((p for p in pagamentos_atualizados if p.mes_referencia == "2025-02"), None)
    assert pagamento_fevereiro is not None
    assert pagamento_fevereiro.data_vencimento == datetime.date(2025, 2, 28)


def test_update_contrato_dia_vencimento_nao_afeta_pagamentos_pagos(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    data_inicio = datetime.date(2025, 1, 1)
    data_fim = datetime.date(2025, 1, 31)
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim.isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 5,
        "tipo_servico_contratado": "Teste Pag Pago"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    contrato_criado = schemas.ContratoServico(**create_response.json())

    pagamentos_response = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    pagamento_original_data = pagamentos_response.json()[0]
    pagamento_original_id = pagamento_original_data["id_pagamento"]
    
    payload_pagar = {
        "status_pagamento": "Pago", "valor_pago": pagamento_original_data["valor_nominal"], 
        "data_pagamento": datetime.date(2025, 1, 3).isoformat()
    }
    client.put(f"/pagamentos/{pagamento_original_id}", headers=headers, json=payload_pagar)

    update_payload_contrato = {"dia_vencimento_mensalidade": 20}
    client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload_contrato)

    get_pag_response = client.get(f"/pagamentos/{pagamento_original_id}", headers=headers)
    assert get_pag_response.status_code == 200
    pagamento_apos_update_contrato = schemas.Pagamento(**get_pag_response.json())

    assert pagamento_apos_update_contrato.status_pagamento == "Pago"
    assert pagamento_apos_update_contrato.data_vencimento == datetime.date.fromisoformat(pagamento_original_data["data_vencimento"])
    assert pagamento_apos_update_contrato.data_vencimento.day == 5


def test_contrato_data_isolation_completo(client: TestClient): # Renomeado para não conflitar com fixture
    headers_op_a = get_operator_token(client, "opA_contr_iso_full")
    escola_a = create_test_escola_for_operator(client, headers_op_a, "EscContrIsoA")
    responsavel_a = create_test_responsavel_for_operator(client, headers_op_a, "RespContrIsoA")
    aluno_a = create_test_aluno_for_operator(client, headers_op_a, escola_a.id_escola, responsavel_a.id_responsavel, "AlunoContrIsoA")
    
    contrato_op_a_data = {
        "id_aluno": aluno_a.id_aluno, "id_responsavel_financeiro": responsavel_a.id_responsavel,
        "data_inicio_contrato": datetime.date.today().isoformat(), "valor_mensal": "350.00",
        "dia_vencimento_mensalidade": 10, "tipo_servico_contratado": "Contrato do Op A para Iso"
    }
    create_resp_a = client.post("/contratos", headers=headers_op_a, json=contrato_op_a_data)
    assert create_resp_a.status_code == 201, create_resp_a.text
    contrato_op_a = schemas.ContratoServico(**create_resp_a.json())

    headers_op_b = get_operator_token(client, "opB_contr_iso_full")

    response_get_b_for_a = client.get(f"/contratos/{contrato_op_a.id_contrato}", headers=headers_op_b)
    assert response_get_b_for_a.status_code == 404

    response_list_b = client.get("/contratos", headers=headers_op_b)
    assert response_list_b.status_code == 200
    assert not any(c["id_contrato"] == contrato_op_a.id_contrato for c in response_list_b.json())

    update_data_b_for_a = {"status_contrato": "Tentativa Update por B"}
    response_put_b_for_a = client.put(f"/contratos/{contrato_op_a.id_contrato}", headers=headers_op_b, json=update_data_b_for_a)
    assert response_put_b_for_a.status_code == 404
    
    response_delete_b_for_a = client.delete(f"/contratos/{contrato_op_a.id_contrato}", headers=headers_op_b)
    assert response_delete_b_for_a.status_code == 404

    response_get_a_for_a = client.get(f"/contratos/{contrato_op_a.id_contrato}", headers=headers_op_a)
    assert response_get_a_for_a.status_code == 200
    assert response_get_a_for_a.json()["tipo_servico_contratado"] == "Contrato do Op A para Iso"

def test_update_contrato_encurtar_data_fim_remove_pagamentos_futuros(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    # Cria contrato de Jan a Mar
    data_inicio = datetime.date(2026, 1, 1)
    data_fim_original = datetime.date(2026, 3, 31)
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim_original.isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 10,
        "tipo_servico_contratado": "Encurtar Contrato"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    contrato_criado = schemas.ContratoServico(**create_response.json())

    # Verifica pagamentos iniciais (Jan, Fev, Mar)
    pagamentos_response_antes = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert len(pagamentos_response_antes.json()) == 3

    # Atualiza contrato para terminar em Fev
    nova_data_fim = datetime.date(2026, 2, 15) # Encurta para terminar em Fev
    update_payload = {"data_fim_contrato": nova_data_fim.isoformat()}
    update_response = client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload)
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["data_fim_contrato"] == nova_data_fim.isoformat()

    # Verifica pagamentos após atualização (deve ter Jan, Fev)
    pagamentos_response_depois = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert pagamentos_response_depois.status_code == 200
    pagamentos_depois = [schemas.Pagamento(**p) for p in pagamentos_response_depois.json()]
    assert len(pagamentos_depois) == 2
    assert any(p.mes_referencia == "2026-01" for p in pagamentos_depois)
    assert any(p.mes_referencia == "2026-02" for p in pagamentos_depois)
    assert not any(p.mes_referencia == "2026-03" for p in pagamentos_depois)


def test_update_contrato_estender_data_fim_gera_novos_pagamentos(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    data_inicio = datetime.date(2026, 1, 1)
    data_fim_original = datetime.date(2026, 1, 31) # Contrato de 1 mês (Jan)
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim_original.isoformat(),
        "valor_mensal": "120.00", "dia_vencimento_mensalidade": 5,
        "tipo_servico_contratado": "Estender Contrato"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    contrato_criado = schemas.ContratoServico(**create_response.json())

    pagamentos_response_antes = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert len(pagamentos_response_antes.json()) == 1 # Pagamento de Jan

    # Atualiza contrato para terminar em Março
    nova_data_fim = datetime.date(2026, 3, 15)
    update_payload = {"data_fim_contrato": nova_data_fim.isoformat()}
    update_response = client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload)
    assert update_response.status_code == 200, update_response.text

    pagamentos_response_depois = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    assert pagamentos_response_depois.status_code == 200
    pagamentos_depois = [schemas.Pagamento(**p) for p in pagamentos_response_depois.json()]
    assert len(pagamentos_depois) == 3 # Jan, Fev, Mar
    assert any(p.mes_referencia == "2026-01" for p in pagamentos_depois)
    assert any(p.mes_referencia == "2026-02" for p in pagamentos_depois)
    assert any(p.mes_referencia == "2026-03" for p in pagamentos_depois)
    for pag in pagamentos_depois:
        assert pag.valor_nominal == Decimal("120.00") # Valor original mantido para novos


def test_update_contrato_valor_mensal_afeta_pagamentos_pendentes(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    data_inicio = datetime.date(2026, 1, 1)
    data_fim = datetime.date(2026, 3, 31) # Contrato de 3 meses (Jan, Fev, Mar)
    valor_original = Decimal("100.00")
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim.isoformat(),
        "valor_mensal": str(valor_original), "dia_vencimento_mensalidade": 10,
        "tipo_servico_contratado": "Mudar Valor Contrato"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    contrato_criado = schemas.ContratoServico(**create_response.json())

    # Marcar o primeiro pagamento (Janeiro) como "Pago" para testar que ele não é afetado
    pagamentos_response_antes = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    pagamentos_antes = [schemas.Pagamento(**p) for p in pagamentos_response_antes.json()]
    pag_jan_original = next((p for p in pagamentos_antes if p.mes_referencia == "2026-01"), None)
    assert pag_jan_original is not None
    
    client.put(f"/pagamentos/{pag_jan_original.id_pagamento}", headers=headers, json={
        "status_pagamento": "Pago", 
        "valor_pago": str(valor_original), 
        "data_pagamento": datetime.date(2026,1,5).isoformat()
    })

    # Atualiza o valor mensal do contrato
    novo_valor_mensal = Decimal("150.00")
    update_payload = {"valor_mensal": str(novo_valor_mensal)}
    update_response = client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload)
    assert update_response.status_code == 200, update_response.text
    assert Decimal(update_response.json()["valor_mensal"]) == novo_valor_mensal

    # Verifica pagamentos após atualização
    pagamentos_response_depois = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    pagamentos_depois = [schemas.Pagamento(**p) for p in pagamentos_response_depois.json()]
    
    pag_jan_depois = next((p for p in pagamentos_depois if p.mes_referencia == "2026-01"), None)
    assert pag_jan_depois is not None
    assert pag_jan_depois.status_pagamento == "Pago" # Não deve ter mudado o status
    assert pag_jan_depois.valor_nominal == valor_original # Não deve ter mudado o valor nominal de um pagamento PAGO

    pag_fev_depois = next((p for p in pagamentos_depois if p.mes_referencia == "2026-02"), None)
    assert pag_fev_depois is not None
    assert pag_fev_depois.status_pagamento != "Pago" # Deve ser Pendente ou Atrasado
    assert pag_fev_depois.valor_nominal == novo_valor_mensal # DEVE ter sido atualizado

    pag_mar_depois = next((p for p in pagamentos_depois if p.mes_referencia == "2026-03"), None)
    assert pag_mar_depois is not None
    assert pag_mar_depois.status_pagamento != "Pago"
    assert pag_mar_depois.valor_nominal == novo_valor_mensal # DEVE ter sido atualizado


def test_update_contrato_status_para_cancelado_cancela_pagamentos_pendentes(client: TestClient, setup_pre_requisitos_contrato):
    headers, aluno, responsavel, _ = setup_pre_requisitos_contrato
    
    data_inicio = datetime.date(2026, 1, 1)
    data_fim = datetime.date(2026, 3, 31)
    contrato_data = {
        "id_aluno": aluno.id_aluno, "id_responsavel_financeiro": responsavel.id_responsavel,
        "data_inicio_contrato": data_inicio.isoformat(), "data_fim_contrato": data_fim.isoformat(),
        "valor_mensal": "100.00", "dia_vencimento_mensalidade": 10,
        "tipo_servico_contratado": "Cancelar Contrato", "status_contrato": "Ativo"
    }
    create_response = client.post("/contratos", headers=headers, json=contrato_data)
    assert create_response.status_code == 201
    contrato_criado = schemas.ContratoServico(**create_response.json())

    # Atualiza status do contrato para Cancelado
    update_payload = {"status_contrato": "Cancelado"}
    update_response = client.put(f"/contratos/{contrato_criado.id_contrato}", headers=headers, json=update_payload)
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["status_contrato"] == "Cancelado"

    # Verifica pagamentos após cancelamento
    pagamentos_response_depois = client.get(f"/pagamentos/por-contrato/{contrato_criado.id_contrato}", headers=headers)
    pagamentos_depois = [schemas.Pagamento(**p) for p in pagamentos_response_depois.json()]
    
    assert len(pagamentos_depois) == 3 # Ainda existem 3 pagamentos, mas seus status devem ter mudado
    for pag in pagamentos_depois:
        assert pag.status_pagamento == "Cancelado"