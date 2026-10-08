# Библиотека в minikube

Команды выполняются из корня проекта в PowerShell. Нужны Docker Desktop (Linux containers), minikube и kubectl.
Результаты фактических проверок записаны в [VERIFICATION.md](VERIFICATION.md).

## 1. Образ приложения

Один Dockerfile собирает `sre-library:1.0.0`: FastAPI, статический веб-интерфейс и Alembic.
Миграции используют тот же образ с другой командой запуска. Для PostgreSQL используется готовый
`postgres:16.8-alpine`, поэтому отдельный Dockerfile для БД не нужен.
Зависимости устанавливаются из `uv.lock`; приложение запускается от UID/GID 10001.

```powershell
docker build -t sre-library:1.0.0 .
docker image inspect sre-library:1.0.0 --format '{{.Id}}'
```

В Compose сервисы `app` и `migrate` также используют этот тег.

## 2. Действия пользователя: docker-env и загрузка образа

Эти действия оставлены пользователю по условию задания.
На момент проверки существующий профиль minikube использовал **containerd**.
Собранный в Docker Desktop образ можно загрузить в этот профиль:

```powershell
minikube image load sre-library:1.0.0
minikube image ls
```

Для варианта из задания с Docker-демоном внутри minikube нужен кластер с Docker runtime.
При создании такого кластера указывают `--container-runtime=docker`. Не удаляйте существующий кластер ради смены runtime:
при необходимости создайте отдельный профиль и используйте его имя вместо `minikube` во всех командах.

Эквивалент `eval $(minikube docker-env)` для PowerShell:

```powershell
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t sre-library:1.0.0 .
```

Настройка действует только в текущем терминале. При сборке внутри Docker runtime minikube образ уже доступен кластеру.
При локальной сборке в Docker Desktop используется `minikube image load`.
Подробности: [официальная инструкция minikube](https://minikube.sigs.k8s.io/docs/handbook/pushing/).
В наших манифестах `imagePullPolicy: Never` запрещает скачивание собственного образа из реестра;
`ErrImageNeverPull` означает, что образ с нужным тегом ещё не загружен в кластер.

## 3. Развёртывание приложения после загрузки образа

| Файл | Ресурсы |
|---|---|
| `00-namespace.yaml` | namespace `library` |
| `01-configmap.yaml` | настройки БД и сервера |
| `02-secret.yaml` | учебный пароль БД и строка подключения |
| `03-postgres.yaml` | PVC на 1 GiB, Service и Deployment PostgreSQL |
| `04-migrate.yaml` | Job `alembic upgrade head` |
| `05-app.yaml` | Deployment с двумя репликами и Service приложения |

Secret содержит только учебные значения. При изменении реквизитов согласованно обновите Secret и ConfigMap.
Для уже инициализированного PVC изменение `POSTGRES_PASSWORD` не меняет пароль внутри PostgreSQL.

Выполняйте блоки по порядку. Если ожидание завершилось ошибкой, сначала устраните причину.

```powershell
kubectl --context minikube apply -f k8s/00-namespace.yaml
kubectl --context minikube apply -f k8s/01-configmap.yaml -f k8s/02-secret.yaml
kubectl --context minikube apply -f k8s/03-postgres.yaml
kubectl --context minikube -n library rollout status deployment/postgres --timeout=180s
```

```powershell
kubectl --context minikube apply -f k8s/04-migrate.yaml
kubectl --context minikube -n library wait --for=condition=complete job/library-migrate --timeout=300s
kubectl --context minikube -n library logs job/library-migrate
```

```powershell
kubectl --context minikube apply -f k8s/05-app.yaml
kubectl --context minikube -n library rollout status deployment/library --timeout=180s
kubectl --context minikube -n library get pods,svc,pvc,jobs
kubectl --context minikube -n library port-forward service/library 8000:80
```

Последняя команда остаётся запущенной в терминале. Откройте <http://localhost:8000/> и <http://localhost:8000/docs>.
В другом терминале проверьте:

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod http://localhost:8000/api/books
```

`startupProbe` даёт серверу время запуститься; liveness проверяет процесс, readiness — доступность БД.
Готовность БД не означает наличие схемы, поэтому ожидание Job обязательно.
PostgreSQL имеет одну реплику и стратегию `Recreate`: два процесса БД не должны одновременно открывать один каталог данных.
PVC использует стандартный StorageClass minikube и сохраняет данные при пересоздании Pod.

## 4. Диагностика, обновление и остановка

```powershell
kubectl --context minikube -n library get events --sort-by=.lastTimestamp
kubectl --context minikube -n library describe deployment library
kubectl --context minikube -n library logs deployment/library --all-pods=true
kubectl --context minikube -n library logs job/library-migrate
kubectl --context minikube -n library get endpointslices -l kubernetes.io/service-name=library
```

При изменении исходников собирайте образ с новым тегом, загрузите его в minikube и обновите тег
в обоих файлах `04-migrate.yaml` и `05-app.yaml`. Для повторного запуска миграции удалите только завершённый Job:

```powershell
kubectl --context minikube -n library delete job library-migrate
kubectl --context minikube apply -f k8s/04-migrate.yaml
kubectl --context minikube -n library wait --for=condition=complete job/library-migrate --timeout=300s
kubectl --context minikube apply -f k8s/05-app.yaml
kubectl --context minikube -n library rollout status deployment/library --timeout=180s
```

Миграции обновления должны быть совместимы с ещё работающей версией приложения. Если совместимости нет,
сначала остановите приложение, уменьшив число реплик до нуля, примените миграции и затем новый Deployment.

Остановка с сохранением PVC и данных:

```powershell
kubectl --context minikube -n library scale deployment library postgres --replicas=0
```

Для возобновления сначала увеличьте число реплик PostgreSQL до 1 и дождитесь готовности, затем приложения до 2.
Удаление namespace `library` или PVC `postgres-data` удалит и сохранённые данные при стандартном StorageClass minikube.
