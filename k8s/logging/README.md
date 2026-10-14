# Сбор логов в VictoriaLogs

## Как это работает

```text
FastAPI / Uvicorn → JSON в stdout → vlagent → VictoriaLogs → веб-интерфейс
```

Приложение пишет логи через structlog: `timestamp`, `level`, `message`, `service.name`, а для HTTP-запросов — метод, путь, статус и длительность. Успешные health-check не логируются.

Сборщик `victoria-logs-collector` (vlagent) работает как DaemonSet на узлах minikube: читает контейнерные логи, добавляет Kubernetes-метаданные и отправляет записи в VictoriaLogs. Собираются только логи контейнера `app` из Pod с меткой `app=library` в namespace `library`.

VictoriaLogs работает в одном экземпляре в namespace `logging` и хранит данные на PVC. Поля `timestamp` и `message` используются как время `_time` и текст `_msg` записи.

## Установка в локальный minikube

Нужны запущенный Docker Desktop, minikube, kubectl и Helm. Приложение с JSON-логированием должно быть развёрнуто по [инструкции Kubernetes](../README.md).

```powershell
minikube start -p sre-docker --driver=docker --container-runtime=docker
kubectl config use-context sre-docker

helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update

helm upgrade --install vls vm/victoria-logs-single --version 0.13.10 -n logging --create-namespace -f k8s/logging/victoria-logs-values.yaml --wait --timeout 5m
helm upgrade --install vlc vm/victoria-logs-collector --version 0.3.8 -n logging -f k8s/logging/collector-values.yaml --wait --timeout 5m
```

Настройки уже заданы в файлах values:

- [victoria-logs-values.yaml](victoria-logs-values.yaml)
- [collector-values.yaml](collector-values.yaml)

Для изменения настроек отредактируйте соответствующий файл и повторите его команду `helm upgrade --install`. Эти файлы передаются Helm через `-f`, применять их через `kubectl apply` не нужно.

## Проверка и просмотр

```powershell
kubectl -n logging get pods,pvc
kubectl -n library logs -l app=library --tail=5
kubectl -n logging port-forward service/victoria-logs 9428:9428
```

Ожидаются готовые Pod, PVC в состоянии `Bound` и JSON-логи приложения. Оставьте port-forward работающим и откройте [интерфейс VictoriaLogs](http://localhost:9428/select/vmui/).

В другом терминале запустите проброс приложения:

```powershell
kubectl -n library port-forward service/library 8000:80
```

В ещё одном терминале создайте запрос:

```powershell
Invoke-RestMethod http://localhost:8000/api/books
```

Через несколько секунд в интерфейсе VictoriaLogs выберите последние 15 минут и выполните LogsQL-запрос:

```text
service.name:="library" AND http.path:="/api/books"
```

Чтобы увидеть все логи приложения, используйте `service.name:="library"`. Если записей нет, проверьте сборщик:

```powershell
kubectl -n logging logs daemonset/victoria-logs-collector --tail=30
```
