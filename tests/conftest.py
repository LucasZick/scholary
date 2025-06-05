# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # Para db_session_test, se não estiver já aqui
import datetime
from typing import Dict, Tuple # Adicionado Tuple

# Importar schemas e app_models uma vez aqui para as fixtures que retornam esses tipos
import schemas
import app_models # Para type hinting e uso direto se necessário

# Suas fixtures existentes (client, db_session_test, setup_test_db_once) devem estar aqui.
# Vou reescrevê-las para garantir que estão completas e como esperamos.

# ---- Configuração do Banco de Dados de Teste e Cliente HTTP ----
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app_models import Base # de app_models/__init__.py
from main import app # Sua instância FastAPI
from core_utils import get_db # A dependência original
import os
from dotenv import load_dotenv

# Adiciona o diretório raiz do projeto ao sys.path
project_dir_conf = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.insert(0, project_dir_conf) # Pytest geralmente lida com isso se executado da raiz

# Carregar variáveis de ambiente
load_dotenv(os.path.join(project_dir_conf, ".env"))

SQLALCHEMY_DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST")
if not SQLALCHEMY_DATABASE_URL_TEST:
    # Tenta carregar de um .env na pasta de testes se não encontrar na raiz ou no ambiente
    test_dotenv_path = os.path.join(os.path.dirname(__file__), '.env.test')
    if os.path.exists(test_dotenv_path):
        load_dotenv(test_dotenv_path)
        SQLALCHEMY_DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST")
    
    if not SQLALCHEMY_DATABASE_URL_TEST:
        # Fallback se ainda não encontrado, ou pode levantar um erro mais forte
        print("AVISO: DATABASE_URL_TEST não configurada, usando SQLite em memória para testes.")
        SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_temp.db"


engine_test = create_engine(SQLALCHEMY_DATABASE_URL_TEST)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_once_for_session():
    # Apaga e recria tabelas uma vez por sessão de teste
    if "sqlite" not in SQLALCHEMY_DATABASE_URL_TEST: # Evita drop_all em memória toda hora se não necessário
        Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    if "sqlite:///./test_temp.db" == SQLALCHEMY_DATABASE_URL_TEST and os.path.exists("./test_temp.db"):
         os.remove("./test_temp.db") # Limpa o arquivo SQLite temporário

@pytest.fixture(scope="function")
def db_session_test() -> Session:
    connection = engine_test.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    try:
        yield db
    finally:
        db.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db_session_test: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session_test
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# ---- Novas Fixtures de Helper ----

def generate_unique_string_conftest(prefix: str = "test_") -> str:
    return f"{prefix}{str(datetime.datetime.now().timestamp()).replace('.', '')}"

@pytest.fixture(scope="function")
def operator_token_fixture_factory(client: TestClient):
    """Retorna uma função que pode ser chamada para criar/logar um operador e obter headers."""
    def _get_operator_token(email_prefix: str) -> Dict[str, str]:
        email = f"{email_prefix}_{generate_unique_string_conftest(str(datetime.datetime.now().microsecond))}@example.com"
        password = "test_fixture_password"
        
        reg_payload = {"email": email, "password": password, "nome_completo": f"Operador Fixture {email_prefix}"}
        # Tenta registrar, não falha criticamente se já existir (o login validará)
        client.post("/users/register", json=reg_payload) 
        
        login_response = client.post("/token", data={"username": email, "password": password})
        if login_response.status_code != 200:
            pytest.fail(f"Fixture: Falha ao obter token para {email}: {login_response.text} (Payload registro: {reg_payload})")
        return {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    return _get_operator_token


@pytest.fixture(scope="function")
def create_escola_fixture_factory(client: TestClient):
    def _create_escola(headers: Dict[str, str], nome_prefix: str = "EscFixture") -> schemas.Escola:
        nome_escola = f"{nome_prefix}_{generate_unique_string_conftest(str(datetime.datetime.now().microsecond))}"[:100]
        cnpj = f"{generate_unique_string_conftest('cnpj_')[:11]}/0001-{generate_unique_string_conftest()[:2]}"[-18:]
        response = client.post(
            "/escolas", headers=headers, json={
                "nome_escola": nome_escola, 
                "endereco_completo": f"Rua Fixture Escola {nome_prefix}",
                "cnpj": cnpj
            }
        )
        if response.status_code != 201: pytest.fail(f"Fixture: Falha ao criar escola '{nome_escola}': {response.text}")
        return schemas.Escola(**response.json())
    return _create_escola

@pytest.fixture(scope="function")
def create_responsavel_fixture_factory(client: TestClient):
    def _create_responsavel(headers: Dict[str, str], cpf_prefix: str = "777Fix") -> schemas.Responsavel:
        cpf = f"{cpf_prefix}{generate_unique_string_conftest()[-7:]}"[-11:]
        email = f"resp_fixture_{cpf_prefix}{generate_unique_string_conftest()}@example.com"
        response = client.post(
            "/responsaveis", headers=headers, json={
                "nome_completo": f"Resp Fixture {cpf_prefix}", "cpf": cpf,
                "email": email, "telefone_principal": "77778888Fix"
            }
        )
        if response.status_code != 201: pytest.fail(f"Fixture: Falha ao criar responsável '{cpf}': {response.text}")
        return schemas.Responsavel(**response.json())
    return _create_responsavel

@pytest.fixture(scope="function")
def create_aluno_fixture_factory(client: TestClient):
    def _create_aluno(headers: Dict[str, str], escola_id: int, responsavel_id: int, nome_prefix: str = "AlunoFixture") -> schemas.Aluno:
        nome_aluno = f"{nome_prefix}_{generate_unique_string_conftest()}"[:100]
        data_nascimento = (datetime.date.today() - datetime.timedelta(days=365*7)).isoformat()
        aluno_payload = {
            "nome_completo_aluno": nome_aluno, "data_nascimento": data_nascimento,
            "id_responsavel_principal": responsavel_id, "id_escola": escola_id,
            "endereco_embarque_predeterminado": f"Casa Fixture {nome_aluno}", "periodo_escolar": "Manhã"
        }
        response = client.post("/alunos", headers=headers, json=aluno_payload)
        if response.status_code != 201: pytest.fail(f"Fixture: Falha ao criar aluno '{nome_aluno}': {response.text} (Payload: {aluno_payload})")
        return schemas.Aluno(**response.json())
    return _create_aluno

@pytest.fixture(scope="function")
def create_motorista_fixture_factory(client: TestClient):
    def _create_motorista(headers: Dict[str, str], cpf_prefix: str = "888Fix") -> schemas.Motorista:
        cnh_validade = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
        motorista_data = {
            "nome_completo": f"Motorista Fixture {cpf_prefix}{generate_unique_string_conftest()[:3]}",
            "cpf": f"{cpf_prefix}{generate_unique_string_conftest()[-7:]}"[-11:],
            "cnh_numero": f"CNHFix{cpf_prefix}{generate_unique_string_conftest()[-4:]}"[-9:],
            "cnh_categoria": "D", "cnh_validade": cnh_validade, "telefone": "88889999",
            "email": f"motor_fixture_{cpf_prefix}{generate_unique_string_conftest()}@example.com"
        }
        response = client.post("/motoristas", headers=headers, json=motorista_data)
        if response.status_code != 201: pytest.fail(f"Fixture: Falha ao criar motorista: {response.text}")
        return schemas.Motorista(**response.json())
    return _create_motorista

@pytest.fixture(scope="function")
def create_van_fixture_factory(client: TestClient):
    def _create_van(headers: Dict[str, str], placa_prefix: str = "FIX") -> schemas.Van:
        # Placa com 7 caracteres (ex: ABC1234)
        placa_sufixo_num = str(datetime.datetime.now().timestamp()).replace('.', '')[-4:]
        placa = f"{placa_prefix.upper()}{placa_sufixo_num}"[:7]

        van_data = {"placa": placa, "modelo_veiculo": "Van Fixture", "marca_veiculo": "Marca Fix", "ano_fabricacao": 2023, "capacidade_passageiros": 15}
        response = client.post("/vans", headers=headers, json=van_data)
        if response.status_code != 201: pytest.fail(f"Fixture: Falha ao criar van '{placa}': {response.text}")
        return schemas.Van(**response.json())
    return _create_van


@pytest.fixture(scope="function")
def setup_pre_requisitos_contrato_fixture(client: TestClient, operator_token_fixture_factory, create_escola_fixture_factory, create_responsavel_fixture_factory, create_aluno_fixture_factory):
    """Fixture que configura um operador, escola, responsável e aluno."""
    headers = operator_token_fixture_factory("op_contr_fix")
    escola = create_escola_fixture_factory(headers, "EscContrFix")
    responsavel = create_responsavel_fixture_factory(headers, "RespContrFix")
    aluno = create_aluno_fixture_factory(headers, escola.id_escola, responsavel.id_responsavel, "AlunoContrFix")
    return headers, aluno, responsavel, escola

# Adicione aqui outras fixtures de setup complexas se necessário, como setup_rota_completa
# ou setup_rota_e_aluno_nao_alocado, adaptando-as para usar as factories acima.

@pytest.fixture(scope="function")
def setup_rota_e_aluno_fixture_factory(client: TestClient, operator_token_fixture_factory, 
                                     create_escola_fixture_factory, create_motorista_fixture_factory,
                                     create_van_fixture_factory, create_responsavel_fixture_factory,
                                     create_aluno_fixture_factory):
    """Retorna uma função que pode criar um setup completo para testes de rota/alocação."""
    def _setup_rota_e_aluno(op_prefix: str = "op_rota_aloc_fix"):
        headers = operator_token_fixture_factory(op_prefix)
        escola = create_escola_fixture_factory(headers, "EscRotaAlocFix")
        motorista = create_motorista_fixture_factory(headers, "MotRotaAlocFix")
        van = create_van_fixture_factory(headers, "VanRotaAlocFix")
        responsavel = create_responsavel_fixture_factory(headers, "RespRotaAlocFix")
        aluno = create_aluno_fixture_factory(headers, escola.id_escola, responsavel.id_responsavel, "AlunoNaoAlocFix")

        rota_data = {
            "nome_rota": f"Rota Aloc Fix {generate_unique_string_conftest()}",
            "id_van_designada": van.id_van,
            "id_motorista_escalado": motorista.id_motorista,
            "id_escola_atendida": escola.id_escola,
            "tipo_rota": "Manhã e Tarde",
        }
        rota_response = client.post("/rotas", headers=headers, json=rota_data)
        if rota_response.status_code != 201:
            pytest.fail(f"Fixture Factory: Falha ao criar rota: {rota_response.text}")
        rota = schemas.Rota(**rota_response.json())
        
        return headers, rota, aluno, escola, responsavel, motorista, van
    return _setup_rota_e_aluno