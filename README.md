# Библиотека

Приложение для учёта экземпляров книг, читателей и выдач. Стек: Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL 16, Alembic; интерфейс — HTML/CSS/JavaScript без сборщика.

## Локальный запуск

Нужны Docker и Docker Compose. Команды выполняются из корня проекта:

```powershell
docker compose up --build -d
docker compose ps
```

- Приложение: [localhost:8000](http://localhost:8000/).
- Документация API: [localhost:8000/docs](http://localhost:8000/docs).
- PostgreSQL: `127.0.0.1:55433`.

Compose запускает БД, выполняет миграции и поднимает приложение. Настройки можно переопределить через `.env` по образцу `.env.example`. Для остановки с сохранением данных:

```powershell
docker compose down
```

## Разработка через uv

Нужны Python 3.12+, uv и доступный PostgreSQL. При первой настройке скопируйте `.env.example` в `.env`; существующий файл сохраняйте. Если приложение Compose уже занимает порт `8000`, сначала остановите его: `docker compose stop app`. Для БД можно использовать сервис Compose:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d --wait db
uv sync --locked --no-install-project
uv run --locked --no-install-project --env-file .env alembic upgrade head
uv run --locked --no-install-project --env-file .env python -m src.server
```

| Переменная | Назначение |
|---|---|
| `DATABASE_URL` | Подключение SQLAlchemy; обязательно при запуске через uv |
| `PORT` | Порт приложения, по умолчанию `8000` |
| `METRICS_PORT` | Порт exporter, по умолчанию `8001` |
| `WEB_CONCURRENCY` | Оставить `1`: registry метрик находится в памяти процесса |
| `LOG_LEVEL` | Уровень логирования, по умолчанию `INFO` |
| `SERVICE_NAME` | Поле `service.name` в логах, по умолчанию `library` |

В Compose передаются `PORT`, `METRICS_PORT` и `WEB_CONCURRENCY`. Для изменения `LOG_LEVEL` и `SERVICE_NAME` в контейнере добавьте их в `environment`. В Kubernetes переменные приложения задаются через ConfigMap и Secret. `.env` не включается в Git и архив сдачи.

Зависимости фиксируются в `pyproject.toml` и `uv.lock`. Для добавления зависимости: `uv add <package>`. Для новой миграции на актуальной БД:

```powershell
uv run --locked --no-install-project --env-file .env alembic revision --autogenerate -m "описание изменения"
```

Проверьте сгенерированный файл перед `alembic upgrade head`. При работе через Compose миграции запускаются командой `docker compose run --rm migrate`.

## API и наблюдаемость

Ресурсы `/api/authors`, `/api/books`, `/api/readers`, `/api/loans` поддерживают список, получение по ID, создание, изменение и удаление. Схемы запросов доступны в `/docs`. Проверки состояния: `/health/live` и `/health/ready`.

Одна книга соответствует физическому экземпляру с уникальным инвентарным номером. Порядок работы: автор → книга → читатель → выдача → возврат. Одновременная активная выдача одного экземпляра запрещена.

Логи записываются в stdout в JSON. Метрики FastAPI, Python и четыре бизнес-счётчика доступны на отдельном порту `8001`, путь `/metrics`. В Compose этот порт не публикуется на хост; при запуске через uv доступен локально. В Kubernetes exporter собирается по Pod IP, а Service приложения публикует только HTTP API.

## Развёртывание и структура

- [k8s/README.md](k8s/README.md) — minikube, PostgreSQL, миграции и приложение.
- [k8s/metrics/README.md](k8s/metrics/README.md) — VictoriaMetrics и команды скринкаста.
- [k8s/logging/README.md](k8s/logging/README.md) — VictoriaLogs и сборщик логов.

Исходный код находится в `src/`: маршруты — `routers/`, операции с БД — `services/`, модели — `models.py`, схемы API — `schemas.py`, метрики — `metrics.py`, интерфейс — `static/`. Миграции находятся в `migrations/`, манифесты и Helm values — в `k8s/`.

## Этапы развития проекта

В [reports](reports/) хранятся отчеты по этапам развития и масштабирования данного проекта. В них можно посмотреть пояснения выбранных решений и подробности реализации.
