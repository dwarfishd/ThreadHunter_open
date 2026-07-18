---
name: Первая фича — MVP парсинг + хранение
description: End-to-end pipeline: CLI init → добавить канал → распарсить Telegram → извлечь контакты → AI-классификация → сохранить в SQLite
type: project
---

Первая фича: CLI-утилита с полным циклом от Telegram-поста до структурированной записи в SQLite.

---

# 2026-07-01-mvp-parsing-pipeline.md

## Контекст

Проект ThreadHunter — CLI для парсинга объявлений из Telegram-каналов швейных производств. Сейчас в репозитории только документация, кода нет. Первая фича — ядро продукта: подключиться к Telegram, получить посты, извлечь контакты и теги, записать в SQLite. Без этого ничто остальное не имеет смысла.

Стек: Python 3.10+, Telethon, SQLite, Typer, Pydantic. AI-классификация — пока через правила/regex, spaCy/Ollama подключаем позже.

## Критерий «фича готова»

1. `th init` — создаёт `.db` и `.env` с шаблоном API-ключей.
2. `th auth` — авторизация Telethon (phone → code → .session).
3. `th add-channel @channel_name` — добавляет канал в БД.
4. `th parse` — подключается к Telegram, парсит настроенные каналы, извлекает контакты (regex), классифицирует теги (rules-based), пишет в SQLite без дубликатов.
5. `th status` — показывает сколько каналов, постов, контактов в базе.
6. Каждая фаза сдаётся с тестами и passing lint/type-check (не откладывать в конец).
7. Покрытие: unit-тесты extraction — 100% ветвей; integration CLI+SQLite — ключевые пути; общее покрытие > 70%.
8. `ruff check src/ tests/` — 0 ошибок, `mypy --strict src/` — 0 ошибок, `pytest` зелёный.

> `th export` в CSV — отдельная фича (следующий план). В MVP не входит.

---

## Фаза 1 — Скелет проекта + CLI каркас [x]

**Цель:** Развернуть Python-проект с Typer-CLI, tox/pytest, mypy, ruff.

**Deliverable:** Команда `th --help` показывает список подкоманд.

**Критерий «сделано»:**
- [x] `pyproject.toml` с зависимостями, entry-point `th`
- [x] `src/threadhunter/` — пакет с `__init__.py`, `cli.py`
- [x] Typer app: `init`, `add-channel`, `parse`, `status`, `export` — пока заглушки с `print()`
- [x] `tests/` — пустая директория с `conftest.py`, `pytest.ini`
- [x] `ruff.toml`, `mypy.ini` — конфигурации линтинга
- [x] `th --help` работает, `th init` печатает "init ok"

**Результат:** ruff check ✅, mypy --strict ✅, pytest ✅ (инфраструктура готова). Замечание: система Python 3.9.6, план требует 3.10+ — `pyproject.toml` стоит обновить до `>=3.10`.

**Оценка:** ~1 час

---

## Фаза 2 — Инициализация БД + модель данных + config [x]

**Цель:** SQLite-схема по memory-model.md, raw SQL миграции, конфиг из .env.

**Deliverable:** `th init` создаёт `threadhunter.db` с таблицами channels, posts, contacts, tags + индексы. Валидирует `.env`.

**Критерий «сделано»:**
- [x] `config.py` — загрузка `.env` через `python-dotenv`, валидация `API_ID` (int), `API_HASH` (non-empty). `th parse` без валидных ключей — fail fast.
- [x] `db/models.py` — Pydantic-модели для Channel, Post, Contact, Tag.
- [x] `db/schema.sql` — CREATE TABLE + CREATE INDEX по memory-model.md.
- [x] `db/connection.py` — `get_db_path()`, `init_db()`, `get_connection()` с foreign_keys + row_factory.
- [x] `th init` создаёт `.db` файл и `.env` из `.env.example`.
- [x] Логирование: INFO → stderr, DEBUG → файл `~/.threadhunter/threadhunter.log`.
- [x] Тест: 4 таблицы + индексы после init (tmp_path).
- [x] Тест: init без `.env` → из шаблона; пустой API_ID → предупреждение.
- [x] Тест: `th parse` без конфига → fail fast.
- [x] `ruff check` — 0 ошибок, `mypy --strict` — 0 ошибок, `pytest` — 29 passed.
- [x] `requires-python = ">=3.10"` исправлено.

**Резюме:** SQLite-схема развёрнута (4 таблицы + 4 индекса). Config с Pydantic-валидацией, fail fast для parse. Логирование. 29 тестов, ruff/mypy чистые. Замечание: `logger.info` в cli.py печатает имя модуля вместо пути к БД — косметика.

**Оценка:** ~2 часа

---

## Фаза 2.5 — Авторизация Telethon (`th auth`) [x]

**Цель:** Пользователь авторизуется в Telegram API, получает рабочую `.session`.

**Deliverable:** `th auth` проводит через flow: phone → code → сохранение сессии.

**Критерий «сделано»:**
- [x] `telegram/auth.py` — `start_auth()` (async), `check_session()` (async), `get_session_path()`.
- [x] `.session` хранится в `~/.threadhunter/`, путь из `TH_SESSION` или `session_name`.
- [x] `th auth` проверяет: если `.session` уже валидна — подтверждает, не пересоздаёт.
- [x] `th parse` перед подключением проверяет сессию → user-friendly error.
- [x] Обработка: CodeInvalidError, SessionPasswordNeededError, FloodWaitError, network retry.
- [x] Тесты: мок успешной авторизации, неверный код, уже авторизован, session cache.
- [x] `ruff check` — 0 ошибок, `mypy --strict` — 0 ошибок, `pytest` — 40 passed.

**Резюме:** Telethon-авторизация работает. `th auth` через typer.prompt. `th parse` проверяет сессию. Обработка ошибок + кэш 5 мин. 40 тестов, ruff/mypy чистые.

**Оценка:** ~2 часа

---

## Фаза 3 — Подключение к Telegram + парсинг каналов [x]

**Deliverable:** `th add-channel` сохраняет канал, `th parse` выкачивает посты через Telethon с пагинацией.

**Критерий «сделано»:**
- [x] `.env.example` с `API_ID=`, `API_HASH=`, `SESSION_NAME=`
- [x] `telegram/client.py` — async Telethon client wrapper, `get_messages` с пагинацией (composite cursor: offset_date + offset_id).
- [x] `channels.py` — CRUD: add_channel, list_channels, update_last_parsed, get_channel_by_id.
- [x] `posts.py` — insert_post (INSERT OR IGNORE), get_latest_post_date, count_posts_by_channel.
- [x] `th add-channel @name` — get_entity + save to DB.
- [x] `th parse` — итерация, fetch, дедупликация, остановка на last_parsed.
- [x] Приватный канал → WARNING + skip.
- [x] Retry: FloodWaitError → sleep, OSError → 3x backoff (1s, 3s, 9s).
- [x] Rate limiting: sleep 1s между каналами.
- [x] Тесты: 5 постов, дедупликация, composite cursor, last_parsed stop, private skip, retry logic.
- [x] `ruff check` — 0 ошибок, `mypy --strict` — 0 ошибок, `pytest` — 75 passed.

**Резюме:** Парсинг работает. Пагинация через composite cursor. Дедупликация INSERT OR IGNORE. Приватные каналы → skip. Retry/backoff. Rate limiting. 75 тестов, ruff/mypy чистые.

**Оценка:** ~3 часа

---

## Фаза 4 — Извлечение контактов + классификация тегов [x]

**Deliverable:** Из raw_text поста извлекаются контакты и теги, записываются в БД.

**Критерий «сделано»:**
- [ ] `extract/contacts.py` — regex для телефонов (+996/7/8 форматы), Telegram username (@...), email. **Дедупликация:** один и тот же контакт (нормализованный телефон/email/username) сохраняется 1 раз в contacts, линкуется на пост через post_contacts (many-to-many).
- [ ] `extract/tags.py` — rules-based классификация из `data/tags-rules.yaml` (не хардкод в Python):
  - location: словарь городов (Бишкек, Ош, Москва, и т.д.)
  - assortment: ключевые слова (футболки, куртки, спецодежда...)
  - offer_type: паттерны ("ищем", "предлагаем", "требуется")
- [ ] `pipeline.py` — orchestrator: fetch → extract contacts → classify tags → store. Pipeline содержит только flow control, бизнес-логика в extract/*.
- [ ] Контакты пишутся в contacts (уникальные), post_contacts линкует на пост.
- [ ] Пост без контактов сохраняется, contacts_count = 0.
- [ ] Тесты: 15+ примеров реальных текстов (из 실제 постов каналов) → ≥ 90% точность извлечения контактов, ≥ 85% точность тегов.
- [ ] Тест: пост без контактов → status корректный.
- [ ] Тест: дубликат контакта в двух постах → 1 запись в contacts, 2 в post_contacts.

**Оценка:** ~3 часа

---

## Фаза 5 — CLI команда status + E2E тест + polish [x]

**Deliverable:** Пользователь видит состояние базы. Полный end-to-end тест pipeline.

**Критерий «сделано»:**
- [x] `th status` — таблица: каналов N, постов M, контактов K, тегов, последний парсинг.
- [x] E2E тест: init → auth (мок) → add-channel → parse (мок) → status → данные корректны.
- [x] `ruff check src/ tests/` — 0 ошибок.
- [x] `mypy --strict src/` — 0 ошибок.
- [x] `pytest --cov=threadhunter --cov-report=term-missing` — **89%** (> 70%).
- [x] README.md с инструкцией: установка, настройка API, `th auth`, запуск.
- [x] `.gitignore` покрывает `*.db`, `.env`, `*.session`, `__pycache__`, `.venv`, `*.log`.
- [x] `.gitignore` не покрывает `data/tags-rules.yaml` (файл правил — часть репо).

---

## Риски

| Риск | Вероятность | Митигация |
|---|---|---|
| Telethon требует ручной авторизации (code из Telegram) | Высокая | `th auth` команда (Фаза 2.5), документировано в README |
| regex не покрывает все форматы телефонов | Средняя | Собирать примеры из реальных постов, расширять паттерны; метрика ≥ 90% |
| rules-based классификация даёт false positive | Средняя | Помечать low-confidence записи, позже заменить на spaCy/Ollama; метрика ≥ 85% |
| Telegram rate limiting | Средняя | Sleep 1s между каналами, retry с exponential backoff |
| SQLite locked при параллельных записях | Низкая | Один процесс, транзакции, retry 5 сек |
| `.session` файл Telethon — где хранится | Высокая | Хранить в `~/.threadhunter/`, путь из `TH_SESSION` |
| Токен сессии истекает | Низкая | `th auth` detect expired → re-prompt; не блокирует parse |
| Приватный канал стал недоступен | Средняя | `th add-channel` проверяет get_entity; parse skip с WARNING |
| Telethon API version совместимость | Низкая | Версия pinned в `pyproject.toml` |

---

## Итог

**Реализовано:** Полный MVP-пайплайн от Telegram-поста до структурированной записи в SQLite. CLI-утилита `th` с командами: init, auth, add-channel, parse, status. Telethon-авторизация, парсинг каналов с пагинацией и дедупликацией, regex-извлечение контактов (+996/+7/8, @telegram, email), rules-based классификация тегов из YAML (location/assortment/offer_type). 118 тестов, 89% покрытие, ruff + mypy --strict чистые.

**Что осталось:** `th export` в CSV — отдельная фича. AI-классификация (spaCy/Ollama) — замена rules-based. `th reprocess` для пересчёта тегов. Бинарники (PyInstaller) — по команде.

**Коммиты:** (не заполнено — git repo не инициализирован)
