#!/bin/sh

# entrypoint.sh

# Verifica se as variáveis de ambiente do PostgreSQL estão definidas
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PORT" ]; then
  echo "Uma ou mais variáveis de ambiente do PostgreSQL não estão definidas."
  exit 1
fi

# Espera o banco de dados ficar pronto
echo "Aguardando o PostgreSQL iniciar..."
# Usaremos 'pg_isready', uma ferramenta do cliente PostgreSQL que precisa ser instalada.
# Vamos adicioná-la ao Dockerfile.
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; do
  echo "Aguardando... o banco de dados não está pronto."
  sleep 2
done

echo "PostgreSQL iniciado com sucesso!"

# Executa as migrações do Alembic
echo "Executando migrações do banco de dados..."
alembic upgrade head

# Inicia a aplicação principal (o comando passado para o script)
echo "Iniciando a aplicação..."
exec "$@"