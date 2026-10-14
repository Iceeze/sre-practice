# Запуск приложения в minikube

Нужны Docker Desktop в режиме Linux containers, minikube и kubectl. Запустите Docker Desktop и откройте PowerShell в корне репозитория — там, где находится `Dockerfile`.

Выполняйте шаги по порядку. После каждой команды ожидания переходите дальше только при успешном завершении. Все команды Kubernetes используют профиль `sre-docker` и namespace `library`.

## 1. Подготовить кластер и образы

Выполните в одном окне PowerShell:

```powershell
minikube start -p sre-docker --driver=docker --container-runtime=docker
kubectl config use-context sre-docker
minikube -p sre-docker docker-env --shell powershell | Invoke-Expression

docker build -t sre-library:1.1.1 .
docker pull postgres:16.8-alpine

docker image ls sre-library
minikube -p sre-docker status
kubectl get nodes
```

Дождитесь состояния узла `Ready`. Образы уже находятся в Docker-демоне minikube, поэтому отдельно загружать их через `image load` не требуется.

## 2. Подготовить namespace к развёртыванию

Создайте namespace.

```powershell
kubectl apply -f k8s/00-namespace.yaml
```

## 3. Применить настройки и запустить PostgreSQL

```powershell
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/03-postgres.yaml

kubectl -n library rollout status deployment/postgres --timeout=180s
kubectl -n library get pods -l app=library-postgres
kubectl -n library get pvc
```

Ожидается один Pod PostgreSQL с `READY 1/1`, статусом `Running` и PVC `postgres-data` со статусом `Bound`.

## 4. Выполнить миграции базы данных

```powershell
kubectl apply -f k8s/04-migrate.yaml

kubectl -n library wait --for=condition=complete job/library-migrate --timeout=300s
kubectl -n library logs job/library-migrate
kubectl -n library get jobs
```

Дождитесь `condition met`. У Job `library-migrate` должно быть `COMPLETIONS 1/1`.

## 5. Запустить приложение

```powershell
kubectl apply -f k8s/05-app.yaml
```

## 6. Проверка pods

```powershell
kubectl -n library rollout status deployment/library --timeout=180s
kubectl -n library get pods
kubectl -n library get deployments,services,pvc,jobs
```

## 7. Увеличить число реплик приложения с двух до четырёх

```powershell
kubectl -n library scale deployment/library --replicas=4
kubectl -n library get pods -l app=library

kubectl -n library rollout status deployment/library --timeout=180s
kubectl -n library get deployment library
kubectl -n library get pods
```

## 8. Открыть приложение и показать работу интерфейса

В текущем терминале запустите проброс порта:

```powershell
kubectl -n library port-forward service/library 8000:80
```

Оставьте команду работающей. После появления `Forwarding from 127.0.0.1:8000` откройте **второе окно PowerShell**:

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Start-Process 'http://localhost:8000/'
```

Обе проверки должны вернуть `status: ok`.

## 9. Сбор логов в VictoriaLogs

Установка официальных Helm charts, проверка JSON-логов и поиск событий описаны в [logging/README.md](logging/README.md). При остановке minikube сбор логов также останавливается; PVC сохраняется до удаления тома или кластера.

## Обновление приложения

После изменения Python-кода соберите образ с новым тегом и обновите Deployment. Например:

```powershell
minikube -p sre-docker image build -t sre-library:1.1.1 .
kubectl -n library set image deployment/library app=sre-library:1.1.1
kubectl -n library rollout status deployment/library --timeout=180s
kubectl -n library get pods -l app=library
```

`set image` сохраняет текущее число реплик. Повторное применение `05-app.yaml` вернёт число реплик к двум, указанным в файле. Если пересобираете тот же тег, после сборки выполните `kubectl -n library rollout restart deployment/library`, затем дождитесь `rollout status`. Для следующих версий обновляйте тег также в манифестах и Compose. При изменении только Python-кода переустанавливать VictoriaLogs и collector не требуется.

## 10. Остановка приложения

В первом терминале остановите `port-forward` сочетанием **Ctrl+C**. Затем остановите кластер:

```powershell
minikube -p sre-docker docker-env --unset --shell powershell | Invoke-Expression
minikube stop -p sre-docker
```

Данные БД сохранятся. Для возобновления существующего кластера выполните `minikube start -p sre-docker`, затем `kubectl config use-context sre-docker` и дождитесь готовности Pod. Повторно применять завершённый Job миграций при этом не нужно.
