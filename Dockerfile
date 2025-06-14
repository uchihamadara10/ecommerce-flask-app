# Use uma imagem base Python
FROM python:3.10-slim-buster # Mantenha a versão 3.10 ou superior

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo requirements.txt e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a pasta 'templates' explicitamente
COPY templates /app/templates

# Copia a pasta 'static' explicitamente
COPY static /app/static

# Copia o restante do código da aplicação (app.py e outros arquivos da raiz)
COPY . .

# Define a variável de ambiente para que o Flask ouça em todas as interfaces
ENV FLASK_APP=app.py

# Expõe a porta que a aplicação vai ouvir (Cloud Run usa a porta 8080 por padrão)
EXPOSE 8080

# Comando para rodar a aplicação quando o contêiner iniciar
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]