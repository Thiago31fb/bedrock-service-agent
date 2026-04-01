FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar apenas o código, excluindo o banco de dados
COPY agent/ ./agent/
COPY app/ ./app/
COPY dataBase/ ./dataBase/

# Criar diretório vazio para o banco (se não existir)
RUN mkdir -p /app/dataBase && \
    # Criar arquivo de banco vazio apenas se não existir
    touch /app/dataBase/agent_metrics.db

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]