# Use uma imagem base Python
FROM python:3.10-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo requirements.txt e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt # Adicionei --no-cache-dir para otimização

# Copia todo o restante do código da aplicação
COPY . .

# Define a variável de ambiente para que o Flask ouça em todas as interfaces
ENV FLASK_APP=app.py
# FLASK_RUN_HOST=0.0.0.0 não é estritamente necessário com gunicorn, mas não atrapalha

# Expõe a porta que a aplicação vai ouvir (Cloud Run usa a porta 8080 por padrão)
EXPOSE 8080

# Comando para rodar a aplicação quando o contêiner iniciar
# Use gunicorn para servir a aplicação Flask em produção
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]