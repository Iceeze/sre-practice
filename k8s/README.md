# Развёртывание в minikube

Нужны Docker Desktop с Linux containers, minikube, kubectl и Helm. Все команды выполняются в PowerShell из корня проекта. После ошибки или неуспешного ожидания к следующему шагу не переходите.

## 1. Кластер и образ приложения

```powershell
minikube start -p sre-docker --driver=docker --container-runtime=docker
kubectl config use-context sre-docker
kubectl get nodes
minikube -p sre-docker image build -t sre-library:1.2.0 .
```

Узел должен быть `Ready`. Образ собирается внутри minikube: `imagePullPolicy: Never` в манифестах приложения и миграций требует его наличия в кластере.

## 2. PostgreSQL

```powershell
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/03-postgres.yaml
kubectl -n library rollout status deployment/postgres --timeout=180s
kubectl -n library get pods,pvc
```

Ожидаются PVC `postgres-data` в состоянии `Bound` и Pod PostgreSQL с `READY 2/2`: БД и postgres-exporter. В `02-secret.yaml` заданы учебные реквизиты; при их изменении согласуйте пароль с `DATABASE_URL`.

## 3. Миграции и приложение

При первом развёртывании:

```powershell
kubectl apply -f k8s/04-migrate.yaml
kubectl -n library wait --for=condition=complete job/library-migrate --timeout=300s
kubectl -n library logs job/library-migrate
kubectl apply -f k8s/05-app.yaml
kubectl -n library rollout status deployment/library --timeout=180s
kubectl -n library get pods,svc
```

Ожидаются две готовые реплики приложения. `library-migrate` со статусом `Completed` — нормальное состояние завершённого Job.

Для повторного выполнения миграций сначала убедитесь, что предыдущий Job завершён, затем пересоздайте его:

```powershell
kubectl -n library delete job library-migrate
kubectl apply -f k8s/04-migrate.yaml
kubectl -n library wait --for=condition=complete job/library-migrate --timeout=300s
```

Если схема не менялась, завершённый Job запускать заново не требуется. Не применяйте изменённый шаблон Job поверх существующего: его поля неизменяемы.

## 4. Доступ и проверка

В отдельном терминале:

```powershell
kubectl -n library port-forward svc/library 8000:80
```

Оставьте его работающим. В другом терминале:

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
```

Ожидается `status: ok`. Интерфейс: [localhost:8000](http://localhost:8000/), API: [localhost:8000/docs](http://localhost:8000/docs).

## Обновление

После изменения Python-кода пересоберите образ. При использовании прежнего тега перезапустите Deployment:

```powershell
minikube -p sre-docker image build -t sre-library:1.2.0 .
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/05-app.yaml
kubectl -n library rollout restart deployment/library
kubectl -n library rollout status deployment/library --timeout=180s
```

Применение `05-app.yaml` устанавливает две реплики. Для нового тега обновите его в манифестах приложения и миграций и в Compose. Изменения PostgreSQL применяются отдельно через `kubectl apply -f k8s/03-postgres.yaml`; стратегия `Recreate` перезапускает Pod БД с прежним PVC.

## Наблюдаемость и остановка

- [metrics/README.md](metrics/README.md) — VictoriaMetrics в namespace `metrics`.
- [logging/README.md](logging/README.md) — VictoriaLogs и collector в namespace `logging`.

Файлы `*-values.yaml` передаются Helm через `-f`; они не являются манифестами для `kubectl apply`. При изменении ConfigMap приложения перезапустите Deployment, чтобы обновились переменные окружения.

Для остановки завершите `port-forward` через `Ctrl+C`, затем выполните:

```powershell
minikube stop -p sre-docker
```

Данные сохраняются. Для продолжения работы достаточно запустить профиль, выбрать контекст и дождаться готовности Pod; переустановка и повторные миграции не нужны.
