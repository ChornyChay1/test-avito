# Используем легковесный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# Переменная окружения для подключения к БД
ENV DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/pr_db

# Открываем порт 8080
EXPOSE 8080

# Команда для запуска сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
