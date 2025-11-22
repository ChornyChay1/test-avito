# PR Reviewer Assignment Service

Сервис назначения ревьюеров для Pull Request’ов. Позволяет автоматически назначать ревьюеров из команды автора, переназначать ревьюеров, получать список PR для пользователя, управлять командами и активностью участников. Взаимодействие исключительно через HTTP API.

---

## Стек

- **Язык:** Python 3.11
- **Фреймворк:** FastAPI
- **База данных:** PostgreSQL
- **ORM:** SQLAlchemy
- **Асинхронный драйвер БД:** asyncpg
- **Миграции:** Alembic
- **Тестирование:** pytest, pytest-asyncio
- **Линтер:** flake8
- **Docker:** контейнеризация сервиса и базы данных

---

## Запуск сервиса

Сервис полностью поднимается через `docker-compose`.

1. Клонируем репозиторий:

```bash
git clone <URL>
cd <repo>
```
 
2. Запуск:

```bash
docker-compose up --build
```

При запуске автоматически выполняются миграции Alembic, сервис доступен на http://localhost:8080.

---

## Тестовая база и запуск тестов

Поднимаем тестовую базу PostgreSQL в Docker:

```bash
docker run --name pr_db_test -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=pr_db_test -p 5433:5432 -d postgres:15
```

Запуск тестов:

```bash
python -m pytest
```

---

## API

### Teams
- **POST /team/add** — создать/обновить команду с участниками.
- **GET /team/get?team_name=<name>** — получить команду и участников.
- **POST /team/deactivate** — массово деактивировать пользователей команды и обновить открытые PR.

### Users
- **POST /users/setIsActive** — изменить активность пользователя.
- **GET /users/getReview?user_id=<id>** — получить PR, назначенные пользователю.

### Pull Requests
- **POST /pullRequest/create** — создать PR и назначить до 2 активных ревьюеров.
- **POST /pullRequest/merge** — выполнить merge PR (идемпотентно).
- **POST /pullRequest/reassign** — переназначить одного ревьювера на другого из команды.

### Stats
- **GET /stats** — получить статистику назначений по пользователям и PR.
- **GET /health** — проверка состояния сервиса.

---

## Примеры использования

### Создание команды:

```json
POST /team/add
{
    "team_name": "backend",
    "members": [
        {"user_id": "u1", "username": "Alice", "is_active": true},
        {"user_id": "u2", "username": "Bob", "is_active": true}
    ]
}
```

### Создание PR:

```json
POST /pullRequest/create
{
    "pull_request_id": "pr-001",
    "pull_request_name": "Fix login",
    "author_id": "u1"
}
```

### Merge PR:

```json
POST /pullRequest/merge
{
    "pull_request_id": "pr-001"
}
```

---

## Тестирование

Запуск тестов:

```bash
pytest
```

- Покрытие: интеграционные и E2E тесты всех основных сценариев.
- Асинхронное тестирование через pytest-asyncio.

---

## Важные особенности и допущения

- Пользователь с `isActive=false` не может быть назначен ревьюером.
- При создании PR назначаются до 2 ревьюеров. Если активных участников меньше двух — назначается доступное количество.
- После merge PR изменение состава ревьюеров запрещено.
- Операция merge идемпотентна.
- Переназначение ревьювера выбирает случайного активного участника из команды заменяемого пользователя.
- Массовая деактивация участников команды обновляет открытые PR, удаляя деактивированных ревьюеров.
- Для удобства и совместимости с Docker используется `python:3.11-slim`.

