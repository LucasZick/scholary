# tests/test_rotas.py
from typing import Dict
import pytest
from fastapi.testclient import TestClient
import datetime
import schemas # Seus Pydantic schemas

# --- Funções Helper ---
# NOTA: Estas funções helper estão se tornando extensas e repetitivas.
# Em um projeto real, elas seriam movidas para conftest.py e injetadas como fixtures.
# Incluindo-as aqui para manter o exemplo autocontido.

def get_operator_token(client: TestClient, email_prefix: str) -> Dict[str, str]:
    email = f"{email_prefix}_{str(datetime.datetime.now().timestamp()).replace('.', '')}@example.com"
    password = "testpassword"
    reg_payload = {"email": email, "password": password, "nome_completo": f"Operador {email_prefix}"}
    client.post("/users/register", json=reg_payload) # Tenta registrar
    
    login_response = client.post("/token", data={"username": email, "password": password})
    if login_response.status_code != 200:
        pytest.fail(f"Falha ao obter token para {email} no helper: {login_response.text} (Registro payload: {reg_payload})")
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}

def generate_unique_string(prefix: str = "test_") -> str:
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

def create_test_escola_for_operator(client: TestClient, headers: Dict[str, str], nome_prefix: str = "EscRota") -> schemas.Escola:
    nome_escola = f"{nome_prefix}_{generate_unique_string(str(datetime.datetime.now().microsecond))}"[:100]
    response = client.post("/escolas", headers=headers, json={"nome_escola": nome_escola, "endereco_completo": f"Rua Escola {nome_prefix}"})
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar escola '{nome_escola}': {response.text}")
    return schemas.Escola(**response.json())

def create_test_motorista_for_operator(client: TestClient, headers: Dict[str, str], cpf_prefix: str = "444R") -> schemas.Motorista:
    cnh_validade = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    motorista_data = {
        "nome_completo": f"Motorista Rota {cpf_prefix}{generate_unique_string()[:3]}",
        "cpf": f"{cpf_prefix}{generate_unique_string()[-7:]}"[-11:],
        "cnh_numero": f"CNHRota{cpf_prefix}{generate_unique_string()[-4:]}"[-9:],
        "cnh_categoria": "D", "cnh_validade": cnh_validade, "telefone": "44445555",
        "email": f"motor_rota_{cpf_prefix}{generate_unique_string()}@example.com"
    }
    response = client.post("/motoristas", headers=headers, json=motorista_data)
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar motorista: {response.text}")
    return schemas.Motorista(**response.json())

def create_test_van_for_operator(client: TestClient, headers: Dict[str, str], placa_prefix: str = "ROT") -> schemas.Van:
    # Garante que a placa gerada tenha no máximo 10 caracteres
    max_suffix_len = 10 - len(placa_prefix)
    if max_suffix_len < 1: # Prefixo já é muito longo
        suffix = ""
    else:
        suffix = generate_unique_string()[-max_suffix_len:]

    placa = f"{placa_prefix}{suffix}"[:10] # Garante o corte final em 10 caracteres

    van_data = {"placa": placa, "modelo_veiculo": "Van Rota Teste", "marca_veiculo": "Marca Rota", "ano_fabricacao": 2022, "capacidade_passageiros": 10}
    response = client.post("/vans", headers=headers, json=van_data)
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar van '{placa}': {response.text}")
    return schemas.Van(**response.json())


def create_test_responsavel_for_operator(client: TestClient, headers: Dict[str, str], cpf_prefix: str = "555R") -> schemas.Responsavel:
    cpf = f"{cpf_prefix}{generate_unique_string()[-7:]}"[-11:]
    email = f"resp_rota_{cpf_prefix}{generate_unique_string()}@example.com"
    response = client.post("/responsaveis", headers=headers, json={"nome_completo": f"Resp Rota {cpf_prefix}", "cpf": cpf, "email": email, "telefone_principal": "55556666"})
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar responsável: {response.text}")
    return schemas.Responsavel(**response.json())

def create_test_aluno_for_operator(client: TestClient, headers: Dict[str, str], escola_id: int, responsavel_id: int, nome_prefix: str = "AlunoRota") -> schemas.Aluno:
    nome_aluno = f"{nome_prefix}_{generate_unique_string()}"[:100]
    data_nascimento = (datetime.date.today() - datetime.timedelta(days=365*7)).isoformat()
    aluno_payload = {
        "nome_completo_aluno": nome_aluno, "data_nascimento": data_nascimento,
        "id_responsavel_principal": responsavel_id, "id_escola": escola_id,
        "endereco_embarque_predeterminado": f"Casa do {nome_aluno}", "periodo_escolar": "Manhã"
    }
    response = client.post("/alunos", headers=headers, json=aluno_payload)
    if response.status_code != 201: pytest.fail(f"Helper: Falha ao criar aluno '{nome_aluno}': {response.text} (Payload: {aluno_payload})")
    return schemas.Aluno(**response.json())

# Fixture para setup completo de uma rota e um aluno (não alocado) para testes de AlunosPorRota
@pytest.fixture(scope="function")
def setup_rota_e_aluno_nao_alocado(client: TestClient):
    headers = get_operator_token(client, "op_rota_aloc")
    escola = create_test_escola_for_operator(client, headers, "EscAloc")
    motorista = create_test_motorista_for_operator(client, headers, "MotAloc")
    van = create_test_van_for_operator(client, headers, "VanAloc")
    responsavel = create_test_responsavel_for_operator(client, headers, "RespAloc")
    aluno_nao_alocado = create_test_aluno_for_operator(client, headers, escola.id_escola, responsavel.id_responsavel, "AlunoNaoAloc")

    rota_data = {
        "nome_rota": f"Rota para Alocacao {generate_unique_string()}",
        "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista,
        "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Manhã e Tarde",
    }
    rota_response = client.post("/rotas", headers=headers, json=rota_data)
    if rota_response.status_code != 201:
        pytest.fail(f"Fixture: Falha ao criar rota para alocação: {rota_response.text}")
    rota = schemas.Rota(**rota_response.json())
    
    return headers, rota, aluno_nao_alocado, escola, responsavel, motorista, van


# Fixture para setup de uma rota válida com todas as dependências
@pytest.fixture(scope="function")
def setup_rota_completa(client: TestClient):
    headers = get_operator_token(client, "op_rota_setup")
    escola = create_test_escola_for_operator(client, headers)
    motorista = create_test_motorista_for_operator(client, headers)
    van = create_test_van_for_operator(client, headers)
    return headers, escola, motorista, van

# --- Testes para CRUD de Rotas ---

def test_create_rota_success(client: TestClient, setup_rota_completa):
    headers, escola, motorista, van = setup_rota_completa
    nome_rota = f"Rota Sucesso {generate_unique_string()}"
    
    rota_data = {
        "nome_rota": nome_rota,
        "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista,
        "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Completa Manhã",
        "horario_partida_estimado": "06:30:00", # HH:MM:SS
        "ativa": True
    }
    response = client.post("/rotas", headers=headers, json=rota_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nome_rota"] == nome_rota
    assert data["id_van_designada"] == van.id_van
    assert data["id_motorista_escalado"] == motorista.id_motorista
    assert data["id_escola_atendida"] == escola.id_escola
    assert "id_rota" in data

def test_create_rota_unauthenticated(client: TestClient, setup_rota_completa):
    _, escola, motorista, van = setup_rota_completa # Precisamos dos IDs válidos
    rota_data = {
        "nome_rota": "Rota Sem Auth", "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Ida"
    }
    response = client.post("/rotas", json=rota_data)
    assert response.status_code == 401, response.text

def test_create_rota_nome_duplicado_mesmo_operador(client: TestClient, setup_rota_completa):
    headers, escola, motorista, van = setup_rota_completa
    nome_rota_duplicado = f"Rota Duplicada {generate_unique_string()}"
    
    rota_data1 = {
        "nome_rota": nome_rota_duplicado, "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Manhã"
    }
    client.post("/rotas", headers=headers, json=rota_data1) # Cria a primeira
    
    # Tenta criar outra com mesmo nome
    van2 = create_test_van_for_operator(client, headers, "ROT2") # Nova van para diferenciar
    rota_data2 = {
        "nome_rota": nome_rota_duplicado, "id_van_designada": van2.id_van, # Pode ser outra van/motorista/escola
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Tarde"
    }
    response = client.post("/rotas", headers=headers, json=rota_data2)
    assert response.status_code == 400, response.text
    assert "Você já possui uma rota com o nome" in response.json()["detail"]

def test_create_rota_van_invalida(client: TestClient, setup_rota_completa):
    headers, escola, motorista, _ = setup_rota_completa # Não usa a van do setup
    rota_data = {
        "nome_rota": "Rota Van Inválida", "id_van_designada": 99999, # ID inválido
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Teste"
    }
    response = client.post("/rotas", headers=headers, json=rota_data)
    assert response.status_code == 400, response.text
    assert "Van fornecida é inválida" in response.json()["detail"]

# Adicione testes similares para id_motorista_escalado inválido e id_escola_atendida inválida

def test_list_minhas_rotas(client: TestClient, setup_rota_completa):
    headers, escola, motorista, van = setup_rota_completa
    client.post("/rotas", headers=headers, json={ # Cria uma rota para garantir que não está vazio
        "nome_rota": f"Rota para Listar {generate_unique_string()}", "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Listagem"
    })
    response = client.get("/rotas", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_minha_rota_by_id(client: TestClient, setup_rota_completa):
    headers, escola, motorista, van = setup_rota_completa
    nome_rota_get = f"Rota para GET {generate_unique_string()}"
    create_response = client.post("/rotas", headers=headers, json={
        "nome_rota": nome_rota_get, "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "GET Teste"
    })
    rota_id = create_response.json()["id_rota"]
    
    response = client.get(f"/rotas/{rota_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_rota"] == rota_id
    assert data["nome_rota"] == nome_rota_get

def test_update_minha_rota(client: TestClient, setup_rota_completa):
    headers, escola, motorista, van = setup_rota_completa
    create_response = client.post("/rotas", headers=headers, json={
        "nome_rota": f"Rota para Update {generate_unique_string()}", "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Update Teste"
    })
    rota_id = create_response.json()["id_rota"]
    
    novo_nome = f"Rota ATUALIZADA {generate_unique_string()}"
    # Cria uma nova van para testar a mudança de van na rota
    nova_van = create_test_van_for_operator(client, headers, "ROTUPD")
    update_data = {"nome_rota": novo_nome, "id_van_designada": nova_van.id_van, "ativa": False}
    
    response = client.put(f"/rotas/{rota_id}", headers=headers, json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_rota"] == rota_id
    assert data["nome_rota"] == novo_nome
    assert data["id_van_designada"] == nova_van.id_van
    assert data["ativa"] == False

def test_delete_minha_rota(client: TestClient, setup_rota_completa):
    headers, escola, motorista, van = setup_rota_completa
    create_response = client.post("/rotas", headers=headers, json={
        "nome_rota": f"Rota para Deletar {generate_unique_string()}", "id_van_designada": van.id_van,
        "id_motorista_escalado": motorista.id_motorista, "id_escola_atendida": escola.id_escola,
        "tipo_rota": "Delete Teste"
    })
    rota_id = create_response.json()["id_rota"]
    
    response = client.delete(f"/rotas/{rota_id}", headers=headers)
    assert response.status_code == 200, response.text # Ou 204 se não retornar conteúdo
    
    get_response = client.get(f"/rotas/{rota_id}", headers=headers)
    assert get_response.status_code == 404, get_response.text

def test_rota_data_isolation(client: TestClient, setup_rota_completa):
    headers_op_a, escola_a, motorista_a, van_a = setup_rota_completa # Setup para Operador A
    
    # Operador A cria uma rota
    rota_op_a_resp = client.post("/rotas", headers=headers_op_a, json={
        "nome_rota": f"Rota Op A {generate_unique_string()}", "id_van_designada": van_a.id_van,
        "id_motorista_escalado": motorista_a.id_motorista, "id_escola_atendida": escola_a.id_escola,
        "tipo_rota": "Isolamento A"
    })
    assert rota_op_a_resp.status_code == 201
    id_rota_op_a = rota_op_a_resp.json()["id_rota"]

    # Operador B
    headers_op_b = get_operator_token(client, "opB_rota_iso")
    # (Opcional: Operador B cria suas próprias entidades se necessário para o teste)

    # Operador B tenta ler a rota do Operador A
    response_get = client.get(f"/rotas/{id_rota_op_a}", headers=headers_op_b)
    assert response_get.status_code == 404 

    # Operador B lista suas rotas (não deve ver a do Operador A)
    response_list = client.get("/rotas", headers=headers_op_b)
    assert response_list.status_code == 200
    rotas_op_b = response_list.json()
    assert not any(r["id_rota"] == id_rota_op_a for r in rotas_op_b)

def test_add_aluno_to_rota_success(client: TestClient, setup_rota_e_aluno_nao_alocado):
    headers, rota, aluno, _, _, _, _ = setup_rota_e_aluno_nao_alocado
    
    aluno_em_rota_data = {
        "id_aluno": aluno.id_aluno,
        "ponto_embarque_especifico": "Em frente à padaria da esquina",
        "status_aluno_na_rota": "Ativo"
        # data_inicio_na_rota pode ser omitido para usar o default do backend (hoje)
    }
    response = client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json=aluno_em_rota_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id_aluno"] == aluno.id_aluno
    assert data["id_rota"] == rota.id_rota
    assert data["ponto_embarque_especifico"] == "Em frente à padaria da esquina"
    assert data["status_aluno_na_rota"] == "Ativo"
    assert "id_aluno_rota" in data

def test_add_aluno_to_rota_aluno_ja_ativo(client: TestClient, setup_rota_e_aluno_nao_alocado):
    headers, rota, aluno, _, _, _, _ = setup_rota_e_aluno_nao_alocado
    
    aluno_em_rota_data = {"id_aluno": aluno.id_aluno}
    # Adiciona o aluno uma vez
    client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json=aluno_em_rota_data)
    
    # Tenta adicionar o mesmo aluno ativo novamente
    response_duplicate = client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json=aluno_em_rota_data)
    assert response_duplicate.status_code == 400, response_duplicate.text
    assert "Este aluno já está ativo nesta rota" in response_duplicate.json()["detail"]

def test_add_aluno_to_rota_aluno_de_outro_operador(client: TestClient, setup_rota_e_aluno_nao_alocado):
    headers_op_a, rota_op_a, _, _, _, _, _ = setup_rota_e_aluno_nao_alocado # Rota do Operador A

    # Cria Operador B e um aluno para ele
    headers_op_b = get_operator_token(client, "opB_aluno_isolado")
    escola_op_b = create_test_escola_for_operator(client, headers_op_b, "EscOpB")
    responsavel_op_b = create_test_responsavel_for_operator(client, headers_op_b, "RespOpB")
    aluno_op_b = create_test_aluno_for_operator(client, headers_op_b, escola_op_b.id_escola, responsavel_op_b.id_responsavel, "AlunoOpB")

    # Operador B tenta adicionar SEU aluno na rota do Operador A
    aluno_em_rota_data = {"id_aluno": aluno_op_b.id_aluno}
    response = client.post(f"/rotas/{rota_op_a.id_rota}/alunos", headers=headers_op_b, json=aluno_em_rota_data)
    # A validação no CRUD de add_aluno_to_rota deve falhar primeiro ao verificar se a rota_op_a pertence ao current_user (Operador B)
    assert response.status_code == 404, response.text # Rota não encontrada PARA O OPERADOR B
    assert "Rota não encontrada ou não pertence a você" in response.json()["detail"]


def test_list_alunos_on_rota(client: TestClient, setup_rota_e_aluno_nao_alocado):
    headers, rota, aluno1, _, _, _, _ = setup_rota_e_aluno_nao_alocado
    
    # Adiciona aluno1 à rota
    client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json={"id_aluno": aluno1.id_aluno})
    
    # Cria e adiciona um segundo aluno à mesma rota
    aluno2 = create_test_aluno_for_operator(client, headers, rota.id_escola_atendida, aluno1.id_responsavel_principal, "AlunoNaRota2") # Reutiliza escola e resp.
    client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json={"id_aluno": aluno2.id_aluno})

    response = client.get(f"/rotas/{rota.id_rota}/alunos", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids_alunos_na_rota = [item["aluno"]["id_aluno"] for item in data]
    assert aluno1.id_aluno in ids_alunos_na_rota
    assert aluno2.id_aluno in ids_alunos_na_rota
    assert data[0]["id_rota"] == rota.id_rota # Verifica se o detalhe da associação está correto

def test_update_aluno_na_rota_details(client: TestClient, setup_rota_e_aluno_nao_alocado):
    headers, rota, aluno, _, _, _, _ = setup_rota_e_aluno_nao_alocado
    
    # Adiciona aluno à rota
    add_response = client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json={"id_aluno": aluno.id_aluno, "ponto_embarque_especifico": "Original"})
    id_aluno_rota = add_response.json()["id_aluno_rota"] # Pega o ID da associação

    update_payload = {"ponto_embarque_especifico": "Ponto Atualizado Teste", "status_aluno_na_rota": "Suspenso"}
    response = client.put(f"/rotas/alunos-associados/{id_aluno_rota}", headers=headers, json=update_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_aluno_rota"] == id_aluno_rota
    assert data["ponto_embarque_especifico"] == "Ponto Atualizado Teste"
    assert data["status_aluno_na_rota"] == "Suspenso"

def test_desativar_aluno_da_rota(client: TestClient, setup_rota_e_aluno_nao_alocado):
    headers, rota, aluno, _, _, _, _ = setup_rota_e_aluno_nao_alocado
    
    add_response = client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json={"id_aluno": aluno.id_aluno})
    id_aluno_rota = add_response.json()["id_aluno_rota"]

    response = client.patch(f"/rotas/alunos-associados/{id_aluno_rota}/desativar", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id_aluno_rota"] == id_aluno_rota
    assert data["status_aluno_na_rota"] == "Inativo"
    assert data["data_fim_na_rota"] == datetime.date.today().isoformat()

    # Tenta adicionar o mesmo aluno novamente (agora deve ser possível, pois o anterior está inativo)
    response_reativar = client.post(f"/rotas/{rota.id_rota}/alunos", headers=headers, json={"id_aluno": aluno.id_aluno, "status_aluno_na_rota": "Ativo"})
    assert response_reativar.status_code == 201, response_reativar.text # Deve permitir criar nova associação ATIVA