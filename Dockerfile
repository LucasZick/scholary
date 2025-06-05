# Dockerfile

FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# NOVO: Instalar dependências do sistema, incluindo postgresql-client para pg_isready
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# NOVO: Torna o script de entrypoint executável dentro do contêiner
RUN chmod +x /app/entrypoint.sh

# NOVO: Define o script de entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8000

# O CMD agora se torna o comando que o entrypoint.sh executará com `exec "$@"`
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]