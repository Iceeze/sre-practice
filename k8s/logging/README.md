# Логи в VictoriaLogs

Цепочка сбора: **приложение → JSON в stdout → vlagent → VictoriaLogs**. Collector работает как DaemonSet и читает контейнер `app` у Pod с меткой `app=library` в namespace `library`. Оба Helm-релиза находятся в namespace `logging`.

## Установка и обновление

Сначала разверните приложение по [k8s/README.md](../README.md). Команды PowerShell выполняются из корня проекта:

```powershell
kubectl config use-context sre-docker
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
helm upgrade --install vls vm/victoria-logs-single --version 0.13.10 -n logging --create-namespace -f k8s/logging/victoria-logs-values.yaml --wait --timeout 5m
helm upgrade --install vlc vm/victoria-logs-collector --version 0.3.8 -n logging -f k8s/logging/collector-values.yaml --wait --timeout 5m
kubectl -n logging get pods,pvc
```

Namespace создаётся Helm. В values заданы VictoriaLogs и vlagent `v1.53.0`, PVC логов, ресурсы, фильтр источников и разбор JSON. Для обновления измените соответствующий values-файл и повторите его команду `helm upgrade --install`.

## Проверка

```powershell
kubectl -n library logs -l app=library -c app --tail=5
kubectl -n logging port-forward svc/victoria-logs 9428:9428
```

Оставьте проброс работающим. В другом терминале:

```powershell
kubectl -n library port-forward svc/library 8000:80
```

В третьем терминале создайте HTTP-событие:

```powershell
Invoke-RestMethod http://localhost:8000/api/books
```

Откройте [VictoriaLogs UI](http://localhost:9428/select/vmui/), выберите последние 15 минут и выполните:

```text
service.name:="library" AND http.path:="/api/books"
```

Основные поля записей: `timestamp` в UTC, `level`, `message`, `service.name`, `http.method`, `http.path`, `http.status_code`, `duration_ms`. Успешные health-check не логируются. Тела запросов, query string и заголовки не записываются.

Если записи не появились:

```powershell
kubectl -n logging logs daemonset/victoria-logs-collector --tail=30
```

Метрики собираются отдельно в VictoriaMetrics: [metrics/README.md](../metrics/README.md). В Compose доступны JSON-логи через `docker compose logs app`; collector и VictoriaLogs там не запускаются.
