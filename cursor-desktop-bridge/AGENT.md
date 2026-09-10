# Для Cursor Cloud Agent

Когда пользователь в чате просит развернуть локальный прототип на ПК:

1. Проверь онлайн: `python3 bridge/status.py --json`
2. Если `desktop_online=true` — ставь задачу без `--allow-offline-queue`
3. Иначе — с `--allow-offline-queue` и сообщи, что задача ждёт watcher на ПК

Пример:

```bash
cd cursor-desktop-bridge
python3 scripts/queue_deploy.py \
  --name "<имя>" \
  --repo "<url>" \
  --branch main \
  --workdir "<путь на ПК>" \
  --command "<команда деплоя>" \
  --allow-offline-queue \
  --json
```

Затем закоммить/запушь `inbox/*.json` если синхронизация через git, либо положи файл в `CURSOR_BRIDGE_DIR` (Dropbox/OneDrive).

Результат читай из `outbox/<task_id>.json`.
