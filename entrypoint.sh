#!/bin/sh

echo "Executando migrações do banco de dados..."
alembic upgrade head

# Inicia a aplicação principal (executa o CMD do Dockerfile)
echo "Iniciando a aplicação com Gunicorn..."
exec "$@"