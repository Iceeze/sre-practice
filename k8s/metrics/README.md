# Метрики

VictoriaMetrics собирает метрики приложения и PostgreSQL каждые 15 секунд. Приложение и БД работают в namespace `library`, VictoriaMetrics — в `metrics`. Отдельный vmagent не требуется.

## Установка и обновление

Нужны запущенный minikube и приложение, развёрнутое по [инструкции](../README.md). Команды выполняются в PowerShell из корня проекта. Если VictoriaMetrics уже установлена и конфигурация не менялась, переходите к проверке.

```powershell
kubectl config use-context sre-docker
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
helm upgrade --install vmsingle vm/victoria-metrics-single -n metrics --create-namespace -f k8s/metrics/guide-vmsingle-values.yaml
```

Namespace создаётся автоматически. После изменения Helm values повторите команду установки и перезапустите VictoriaMetrics:

```powershell
kubectl -n metrics rollout restart statefulset/vmsingle-victoria-metrics-single-server
kubectl -n metrics rollout status statefulset/vmsingle-victoria-metrics-single-server --timeout=180s
```

## 1. Проверка ресурсов

Проверьте Pod, Service и хранилище:

```powershell
kubectl config use-context sre-docker
kubectl -n metrics get pods
kubectl -n metrics get svc,pvc
kubectl -n library get pods
```

Дождитесь VictoriaMetrics со статусом `Running` и `READY 1/1`, хранилища со статусом `Bound`, двух готовых реплик приложения и Pod PostgreSQL с `READY 2/2`.

## 2. Доступ к VictoriaMetrics и приложению

В первом окне PowerShell запустите проброс порта VictoriaMetrics:

```powershell
kubectl -n metrics port-forward svc/vmsingle-victoria-metrics-single-server 8428:8428
```

Во втором окне запустите проброс портов приложения:

```powershell
kubectl -n library port-forward deployment/library 8000:8000 8001:8001
```

Оба окна оставьте работающими. Для следующих команд откройте третье окно PowerShell.

Доступные страницы:

- [Приложение](http://localhost:8000/).
- [Метрики приложения](http://localhost:8001/metrics).
- [Состояние сбора — targets](http://localhost:8428/targets).
- [Запросы и графики — vmui](http://localhost:8428/vmui/).

## 3. Проверка сбора метрик

Откройте страницу targets. В группе `kubernetes-pods` должны быть три адреса: две реплики приложения на порту `8001` и postgres-exporter на порту `9187`. Все три должны иметь состояние `UP`.

В третьем окне получите список имён сохранённых метрик:

```powershell
curl.exe "http://localhost:8428/api/v1/label/__name__/values"
```

Проверьте успешный сбор, доступность PostgreSQL и метрики Python:

```powershell
curl.exe "http://localhost:8428/api/v1/query?query=up"
curl.exe "http://localhost:8428/api/v1/query?query=pg_up"
curl.exe "http://localhost:8428/api/v1/query?query=python_info"
```

В ответах должно быть `"status":"success"` и непустой `result`. В паре `value` первое число — время, второе — значение метрики. Для `up`, `pg_up` и `python_info` ожидается значение `1`. Запрос `up` также покажет другие targets Kubernetes.

Чтобы проверить HTTP-метрики, откройте приложение, перейдите в раздел книг и подождите 15–30 секунд:

```powershell
curl.exe "http://localhost:8428/api/v1/query?query=http_requests_total"
```

Те же имена метрик можно вводить по одному в vmui и просматривать результат в таблице или на графике.

## 4. Проверка бизнес-метрик

Посмотрите текущие значения четырёх счётчиков:

```powershell
curl.exe "http://localhost:8428/api/v1/query?query=sum(library_books_created_total)"
curl.exe "http://localhost:8428/api/v1/query?query=sum(library_readers_registered_total)"
curl.exe "http://localhost:8428/api/v1/query?query=sum(library_loans_created_total)"
curl.exe "http://localhost:8428/api/v1/query?query=sum(library_loans_returned_total)"
```

`sum` складывает значения обеих реплик приложения.

В интерфейсе приложения выполните действия по порядку:

1. Создайте автора.
2. Добавьте книгу с новым инвентарным номером.
3. Зарегистрируйте читателя с новым телефоном.
4. Оформите выдачу книги.
5. Нажмите «Вернуть» у этой выдачи.

Подождите 15–30 секунд и повторите четыре команды выше. Каждый счётчик должен увеличиться на `1`, если параллельно не выполнялись другие операции.

## Завершение и диагностика

Остановите пробросы портов через `Ctrl+C` в первых двух окнах. Приложение и сбор метрик внутри кластера продолжат работать.

Если метрики не появились, проверьте ошибки на странице targets и логи:

```powershell
kubectl -n library logs deployment/postgres -c postgres-exporter --tail=20
kubectl -n metrics logs statefulset/vmsingle-victoria-metrics-single-server --tail=20
```
