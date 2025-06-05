# tests/test_auth.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # Necessário para type hinting, mas a fixture injeta
import schemas # Seus schemas Pydantic (para verificar a resposta)

# As fixtures 'client' e 'db_session_test' serão injetadas automaticamente pelo pytest
# com base nos seus nomes e na definição em conftest.py

USER_TEST_EMAIL = "testauthuser@example.com"
USER_TEST_PASSWORD = "testpassword123"

def test_create_user(client: TestClient): # pytest injeta a fixture 'client'
    response = client.post(
        "/users/register", # Endpoint de registro do seu auth_router.py
        json={
            "email": USER_TEST_EMAIL,
            "password": USER_TEST_PASSWORD,
            "nome_completo": "Auth Test User",
            "is_active": True,
            "is_superuser": False
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == USER_TEST_EMAIL
    assert "id_user" in data
    assert "hashed_password" not in data # Senha não deve ser retornada

def test_create_existing_user_email(client: TestClient):
    # Usuário já foi criado no teste anterior (ou crie de novo se os testes não forem sequenciais ou se o DB limpar entre eles)
    # Como usamos rollback por teste, o usuário do teste anterior não existe mais.
    # Então, precisamos criar o usuário aqui novamente para testar a duplicidade.
    client.post(
        "/users/register",
        json={"email": "duplicate@example.com", "password": USER_TEST_PASSWORD},
    )
    response = client.post(
        "/users/register",
        json={"email": "duplicate@example.com", "password": USER_TEST_PASSWORD},
    )
    assert response.status_code == 400, response.text
    assert "Email já registrado" in response.json()["detail"]


def test_login_for_access_token(client: TestClient):
    # Garante que o usuário de teste existe
    client.post(
        "/users/register",
        json={
            "email": USER_TEST_EMAIL, # Use o mesmo email do test_create_user se quiser
            "password": USER_TEST_PASSWORD,
            "nome_completo": "Auth Test User Login",
        },
    )
    
    login_data = {
        "username": USER_TEST_EMAIL, # Lembre-se que o form espera 'username' para o email
        "password": USER_TEST_PASSWORD,
        # grant_type=password é adicionado automaticamente pelo TestClient ao enviar 'data='
    }
    response = client.post("/token", data=login_data) # Envia como form data
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient):
    client.post( # Cria o usuário
        "/users/register",
        json={"email": "wrongpass@example.com", "password": "correctpassword"},
    )
    response = client.post(
        "/token",
        data={"username": "wrongpass@example.com", "password": "incorrectpassword"}
    )
    assert response.status_code == 401, response.text
    assert "Email ou senha incorretos" in response.json()["detail"]

def test_login_user_not_found(client: TestClient):
    response = client.post(
        "/token",
        data={"username": "nonexistent@example.com", "password": "somepassword"}
    )
    assert response.status_code == 401, response.text # Ou 404 dependendo da sua implementação, 401 é comum
    assert "Email ou senha incorretos" in response.json()["detail"]

def test_read_users_me_success(client: TestClient):
    # 1. Cria um usuário e faz login para obter o token
    email_me = "me_user@example.com"
    password_me = "passwordForMe"
    client.post(
        "/users/register",
        json={"email": email_me, "password": password_me, "nome_completo": "Me User"},
    )
    login_response = client.post("/token", data={"username": email_me, "password": password_me})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Chama /users/me com o token
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == email_me
    assert data["nome_completo"] == "Me User"
    assert "id_user" in data
    assert "hashed_password" not in data # Importante!

def test_read_users_me_unauthenticated(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text # "Not authenticated"

def test_create_user_invalid_email(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "invalidemail", # Email sem formato válido
            "password": "validpassword123",
            "nome_completo": "Invalid Email User",
        },
    )
    assert response.status_code == 422, response.text # Erro de validação da Pydantic
    data = response.json()
    assert "detail" in data
    # Pydantic V2 retorna um objeto de erro mais detalhado
    # A estrutura pode variar um pouco, mas geralmente tem 'loc' e 'msg'
    assert any("value is not a valid email address" in err.get("msg", "").lower() for err in data["detail"])


def test_create_user_short_password(client: TestClient):
    # Este teste depende da validação min_length=8 no schema UserCreate
    response = client.post(
        "/users/register",
        json={
            "email": "shortpass@example.com",
            "password": "short", # Senha com menos de 8 caracteres
            "nome_completo": "Short Password User",
        },
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data
    assert any("String should have at least 8 characters" in err.get("msg", "") for err in data["detail"])


def test_login_inactive_user(client: TestClient):
    inactive_email = "inactive@example.com"
    inactive_password = "password123"
    # Cria um usuário inativo
    client.post(
        "/users/register",
        json={
            "email": inactive_email,
            "password": inactive_password,
            "nome_completo": "Inactive User",
            "is_active": False # Define como inativo na criação
        },
    )
    
    login_data = {"username": inactive_email, "password": inactive_password}
    response = client.post("/token", data=login_data)
    
    assert response.status_code == 400, response.text # Conforme definido no auth_router
    assert "Usuário inativo" in response.json()["detail"]

def test_create_superuser(client: TestClient):
    superuser_email = "super@example.com"
    superuser_password = "superpassword123"
    response = client.post(
        "/users/register",
        json={
            "email": superuser_email,
            "password": superuser_password,
            "nome_completo": "Super User Test",
            "is_superuser": True # Define como superusuário
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == superuser_email
    assert data["is_superuser"] is True

    # (Opcional) Verifica se /users/me retorna is_superuser corretamente
    login_response = client.post("/token", data={"username": superuser_email, "password": superuser_password})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["is_superuser"] is True
