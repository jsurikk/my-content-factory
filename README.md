# 🏭 Content Factory — Фабрика Контента

> AI-система, которая пишет контент в твоём голосе. Посты, сценарии, карусели, статьи — по проверенным методикам, а не из головы.

**Автор:** Макс Галсон • [galson.pro](https://galson.pro) • [Telegram](https://t.me/galsonproai)

---

## ⏱ За 1 час у тебя будет

✅ AI-агент, который знает твой голос и аудиторию  
✅ 15+ скиллов с методиками контента (Threads, YouTube, Reels, карусели...)  
✅ Notion-шаблон для управления постами  
✅ Система самообучения — чем больше работаешь, тем точнее контент  
✅ Опционально: автопостинг в Threads по расписанию  

---

## 🚀 Быстрый старт

> **👉 [GETTING-STARTED.md](./GETTING-STARTED.md) — полный путь от скачивания до первого контента за 30 минут**

### Выбери свой вариант

### Вариант A: Claude Code (терминал)

Для тех, кто работает с Claude Code в терминале или VS Code.

1. Открой конструктор: https://github.com/maximgalson/content-factory
2. Нажми зелёную кнопку **"Use this template"** → **"Create a new repository"**
3. Назови как хочешь (например `my-content-factory`), нажми **Create**
4. Склонируй СВОЮ копию:
```bash
git clone https://github.com/ТВОЙ_ЮЗЕРНЕЙМ/my-content-factory.git
cd my-content-factory/claudecode-content-factory
claude
```

Напиши `начать` — Claude проведёт интервью за 10 минут и сгенерирует первые посты.

📖 **Полная инструкция:** [claudecode-content-factory/INSTALL.md](./claudecode-content-factory/INSTALL.md)  
⚡ **Быстрый старт:** [claudecode-content-factory/QUICK-START.md](./claudecode-content-factory/QUICK-START.md)

**Требования:**
- [Claude Max](https://claude.ai/pricing) ($100/мес) или Anthropic API ключ
- [Node.js 18+](https://nodejs.org)
- Claude Code (`npm install -g @anthropic-ai/claude-code`)

---

### Вариант B: OpenClaw (Telegram)

Для тех, кто хочет работать прямо из Telegram. Не нужен терминал.

📖 **Установка на Mac/Linux:** [openclaw-content-factory/SETUP.md](./openclaw-content-factory/SETUP.md)  
📖 **Установка на VPS (24/7):** [openclaw-content-factory/VPS-INSTALL.md](./openclaw-content-factory/VPS-INSTALL.md)  
📖 **Гайд по OpenClaw + Telegram:** [galson.pro/guides/openclaw-telegram](https://galson.pro/guides/openclaw-telegram)

**Требования:**
- Anthropic API ключ ([console.anthropic.com](https://console.anthropic.com)) — ~$20-50/мес по использованию
- [OpenClaw](https://openclaw.ai)
- Telegram бот (бесплатно через [@BotFather](https://t.me/BotFather))

---

## 📦 Что внутри

```
content-factory/
├── claudecode-content-factory/    ← Версия для Claude Code
│   ├── CLAUDE.md                  ← Мозг системы
│   ├── skills/                    ← 15+ скиллов с методиками
│   ├── agents/                    ← Виртуальная команда
│   ├── projects/                  ← Твои проекты (голос, обучение)
│   ├── tools/                     ← Threads Scheduler и др.
│   ├── INSTALL.md                 ← Пошаговая установка
│   ├── QUICK-START.md             ← За 15 минут до первого поста
│   └── docs/                      ← Документация
│
├── openclaw-content-factory/      ← Версия для OpenClaw (Telegram)
│   ├── workspace/                 ← Рабочее пространство агента
│   ├── skills/                    ← 15 скиллов
│   ├── SETUP.md                   ← Установка на Mac/Linux
│   └── VPS-INSTALL.md             ← Установка на VPS (24/7)
│
├── cursor-desktop-bridge/         ← Мост Cursor Chat ↔ десктоп (очередь задач)
│   ├── README.md                  ← Файловый обмен / HTTP API / deploy прототипа
│   ├── bridge/                    ← enqueue, watcher, status, server
│   └── scripts/                   ← queue_deploy.py, selftest.py
│
└── README.md                      ← Ты здесь
```

### 15 скиллов (методик контента)

| Скилл | Что делает |
|-------|-----------|
| **threads** | Посты для Meta Threads + Notion шаблон + автопостинг |
| **youtube** | Сценарии, SEO, хуки, удержание, монтаж |
| **reels** | Вертикальный контент (Reels / Shorts / TikTok) |
| **carousel** | Instagram карусели (структура, CTA, промпты) |
| **storytelling** | Сторителлинг с 18 психологическими триггерами |
| **selling-meanings** | Продающие смыслы, формулы копирайтинга |
| **offer** | Формулировка ядра оффера (методология Hormozi) |
| **customer-research** | Распаковка смыслов — карта 8 столбиков |
| **launch** | Система запусков продуктов (PLF × Тимочко) |
| **nano-banana** | Промпты для Midjourney |
| **heygen** | AI-аватары с озвучкой |
| **veo-video** | Генерация видео через Veo 3.1 |
| **prompt-engineer** | Создание и оптимизация промптов |
| **seo-blog-writer** | SEO-статьи для блога |
| **swipefile** | Разбор видео/контента в Notion (16 секций + черновики) |
| **creator** | Создатель AI-агентов |
| **memory-system** | Настройка и контроль памяти агента |

### Как это работает

```
Твои слова → Конструктор выбирает методику → Добавляет твой голос → Контент
```

1. **Интервью** — система узнаёт кто ты, для кого пишешь, как говоришь
2. **Генерация** — пишешь `threads 5` и получаешь 5 постов по методике
3. **Обратная связь** — говоришь `это сработало` / `это не сработало`
4. **Улучшение** — с каждым разом контент точнее попадает в твой стиль

---

## 🔄 Обновление

### Обновление конструктора

Конструктор обновляется через скачивание новой версии:
1. Скачай свежую версию: https://github.com/maximgalson/content-factory → Code → Download ZIP
2. Распакуй и скопируй `skills/` поверх своих (brand/ и learning/ НЕ трогай)

Подробнее: [claudecode-content-factory/UPDATE-GUIDE.md](./claudecode-content-factory/UPDATE-GUIDE.md)

---

## 📋 Что нового (v1.18 — 20 февраля 2026)

- ✅ **15+ скиллов** — полный набор методик контента
- ✅ **OpenClaw версия** — полноценная работа через Telegram
- ✅ **Регламент** — агент всегда использует методики, не пишет из головы
- ✅ **Notion шаблон Threads** — готовая база для управления постами
- ✅ **Threads Scheduler** — автопостинг из Notion в Threads
- ✅ **Самодиагностика** — агент проверяет скиллы при первом запуске

📖 **[Как обновить → UPDATE-GUIDE.md](./UPDATE-GUIDE.md)** | **[История обновлений → CHANGELOG.md](./CHANGELOG.md)**

---

## ❓ FAQ

**Нужен ли опыт программирования?**  
Нет. Для OpenClaw достаточно уметь писать в Telegram. Для Claude Code — пара команд в терминале (всё описано в инструкции).

**Сколько стоит?**  
Конструктор бесплатный. Нужна подписка Claude ($100/мес) или API ключ (~$20-50/мес по использованию).

**Посты не похожи на меня?**  
Скажи `интервью` — перенастроим голос. Или покажи примеры своих текстов.

**Как обновить?**  
Скачай свежую версию ZIP с GitHub, скопируй `skills/` поверх своих. Твои данные (brand, learning) не затрагиваются.

**Работает на русском?**  
Да, полностью.

---

## 🆘 Поддержка

- **Бот поддержки:** [@galsonproAIbot](https://t.me/galsonproAIbot?start=support)
- **Канал:** [@galsonproai](https://t.me/galsonproai)
- **Гайды:** [galson.pro/guides](https://galson.pro/guides)
- **Автор:** [@maximgalson](https://t.me/maximgalson)

---

## Лицензия

Проприетарная лицензия. Конструктор для личного использования. Распространение запрещено.

---

*© Фабрика Контента v1.18 | Макс Галсон | [galson.pro](https://galson.pro)*
