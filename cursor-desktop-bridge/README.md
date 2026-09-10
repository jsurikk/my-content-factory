# Cursor ↔ Desktop Bridge

Мост между этим чатом (Cursor Cloud Agent) и десктоп-приложением на вашем компьютере.

Вы ставите задачу здесь → агент кладёт JSON в очередь → приложение на ПК (когда онлайн) забирает задачу по **дате файла** или через **HTTP API** и разворачивает локальный прототип.

## Как это работает

```
Cursor Chat (этот агент)
        │
        │  python scripts/queue_deploy.py --name my-proto ...
        ▼
   bridge/inbox/task_....json     ← очередь (mtime = приоритет по свежести)
        │
        │  watcher на ПК (poll 2с) или HTTP API
        ▼
   processing/ → handlers → outbox/task_....json
        │
        ▼
   Агент читает статус / результат
```

Три транспорта (можно совмещать):

| Транспорт | Когда использовать | Как синхронизировать |
|-----------|--------------------|----------------------|
| **Файлы + mtime** | Самый простой, без серверов | Git pull/push, Dropbox, OneDrive, Syncthing, общая папка |
| **HTTP API** | ПК доступен по сети / туннелю / VPS | `bridge/server.py` на ПК или на облаке + общая `bridge_dir` |
| **Cursor Private Worker** | Официальный путь Cursor | `cursor worker start` на ПК — агент сам работает локально |

## Быстрый старт на ПК

```bash
cd cursor-desktop-bridge
cp config.example.json config.json
# укажите deploy-команду в handlers.deploy_local_prototype.command
python bridge/watcher.py
```

В другом терминале (или из этого чата после sync):

```bash
python scripts/queue_deploy.py --name demo-proto --allow-offline-queue --json
python bridge/status.py
```

Watcher увидит новый файл в `inbox/` (по `mtime`), заберёт задачу и положит результат в `outbox/`.

## Команды

### Поставить задачу «развернуть локальный прототип»

```bash
python scripts/queue_deploy.py \
  --name my-landing \
  --repo https://github.com/you/repo \
  --branch main \
  --workdir "C:/protos/my-landing" \
  --command "npm install && npm run dev" \
  --allow-offline-queue
```

Если десктоп **онлайн** (heartbeat свежий), `--allow-offline-queue` не нужен — задача уйдёт сразу.

### Пинг / произвольная команда

```bash
python bridge/enqueue.py --type ping --payload "{\"hello\":true}" --allow-offline-queue
python bridge/enqueue.py --type run_command --payload "{\"command\":\"echo hi\",\"shell\":true}" --allow-offline-queue
```

### Статус

```bash
python bridge/status.py --json
```

### HTTP API (опционально)

```bash
pip install -r requirements.txt
export BRIDGE_API_TOKEN=secret
python bridge/server.py --host 0.0.0.0 --port 8787
```

```bash
curl -H "Authorization: Bearer secret" \
  -H "Content-Type: application/json" \
  -d '{"type":"deploy_local_prototype","payload":{"prototype":"demo"},"allow_offline_queue":true}' \
  http://127.0.0.1:8787/tasks
```

Для доступа из облака: Cloudflare Tunnel / ngrok / VPS с токеном. Платные облака (Railway, Fly.io, Render) тоже подходят: API пишет в том же `bridge_dir`, а watcher на ПК читает файлы через sync.

## Конфиг `config.json`

```json
{
  "poll_interval_sec": 2,
  "heartbeat_max_age_sec": 30,
  "worker_id": "desktop-main",
  "http": { "host": "127.0.0.1", "port": 8787, "token": "change-me" },
  "handlers": {
    "deploy_local_prototype": {
      "workdir": "C:/protos",
      "command": "npm install && npm run dev",
      "timeout_sec": 600
    }
  }
}
```

Переменная окружения `CURSOR_BRIDGE_DIR` перекрывает путь к корню моста (удобно для Dropbox: `D:/Dropbox/cursor-bridge`).

## Сценарий «я пишу в чат — задача появляется на ПК»

1. На ПК постоянно крутится `python bridge/watcher.py` (можно положить в автозагрузку / `start_watcher.bat`).
2. Папка `cursor-desktop-bridge` синхронизируется с облаком агента через **git** (этот репозиторий) или через Dropbox/OneDrive.
3. В чате вы пишете: «разверни локальный прототип X».
4. Агент вызывает `scripts/queue_deploy.py` (или коммитит JSON в `inbox/`) и пушит.
5. На ПК watcher/sync видит новый/обновлённый файл → claim → deploy → `outbox/`.
6. Агент читает `outbox` и сообщает результат.

Если ПК офлайн — задача остаётся в `inbox` со статусом `offline_pending` и подхватится, как только появится heartbeat.

## Windows: автозапуск watcher

`start_watcher.bat`:

```bat
@echo off
cd /d "%~dp0"
set CURSOR_BRIDGE_DIR=%~dp0
python bridge\watcher.py
```

## Безопасность

- По умолчанию `deploy_local_prototype` без настроенной команды работает в **dry_run** (ничего не выполняет на ПК).
- HTTP API защищайте Bearer-токеном; не открывайте порт в интернет без туннеля/auth.
- `run_command` выполняет shell на ПК — включайте только если доверяете источнику задач.

## Связь с Cursor Private Workers

Если нужен полноценный агент прямо на машине (не только очередь задач), на ПК:

```bash
cursor worker start
```

Тогда Cloud Agent может работать на вашем компьютере нативно. Этот bridge полезен, когда у вас **своё** десктоп-приложение / свой пайплайн деплоя прототипов и нужна тонкая очередь задач.
