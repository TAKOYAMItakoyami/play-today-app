FROM python:3.12-slim

WORKDIR /app

# Устанoвка системных зависимостей для psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000

# Gunicorn с ASGI-воркерами Uvicorn для поддержки async-маршрутов
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "asgi:application"]