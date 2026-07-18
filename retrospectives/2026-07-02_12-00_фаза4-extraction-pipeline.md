# Ретроспектива: Фаза 4 — Извлечение контактов + классификация тегов

**Дата:** 2026-07-02 12:00 | **Длительность:** ~3 часа | **План:** plans/2026-07-01-mvp-parsing-pipeline.md

## Что сделали

- `extract/contacts.py` — regex для телефонов (+996/+7/8), @telegram, email + нормализация
- `extract/tags.py` — rules-based классификатор из `data/tags-rules.yaml` (location/assortment/offer_type)
- `pipeline.py` — orchestrator: `process_post`, `process_channel`, `run_pipeline`
- `data/tags-rules.yaml` — 24 города, 20 типов одежды, 15 паттернов offer_type
- `schema.sql` — `UNIQUE(type, value, post_id)` на contacts, таблица `post_contacts`
- `cli.py` — `th parse` вызывает `process_channel` после загрузки постов
- `pyproject.toml` — добавлена зависимость `pyyaml>=6.0`
- 40 тестов для Фазы 4 (всего 115)
- ruff clean, mypy --strict clean, pytest 115 passed

## Реальные проблемы (3) — доказаны и починены

| # | Проблема | Почему реально для НАШЕГО проекта | Фикс |
|---|---|---|---|
| 1 | `\w` в Telegram regex включал кириллицу | `@иванов` матчился как username. Telegram username'ы строго ASCII. Пользователь увидит мусор в контактах. | `[A-Za-z0-9_]` вместо `\w` |
| 2 | `fetchall()` грузил все посты в RAM | 100K постов = 111 MB vs 2.2 MB у `fetchmany`. На старте 200 постов — несущественно, но при росте OOM. | `cursor.fetchmany(1000)` + shared connection |
| 3 | conn-per-post: 209x медленнее batch | 44 сек vs 0.2 сек на 100K постов. Пользователь ждёт `th parse` — думает, что зависло. | `_conn` parameter + один conn на канал |

## Вычеркнуты (4) — теоретические, не для MVP

| # | Проблема | Почему вычеркнут |
|---|---|---|
| 4 | Нет `processed_at` → повторная обработка | 200 постов × 5 каналов = 1000 строк. INSERT OR IGNORE = 50ms. Экономим 50ms, добавляем 40 строк кода + миграцию навсегда. |
| 5 | `process_channel` для непарсеных каналов | 0.88ms на холостой вызов при 20K постах. `WHERE processed_at IS NULL` → 0 строк. Несущественно. |
| 6 | Нет команды `th reprocess` | Фича, не баг. На старте rules.yaml меняется 1–2 раза. Пересчёт = `UPDATE posts SET processed_at = NULL` или удалить БД. |
| 7 | O(rules × text) классификация | 59 правил × 164 символа = 0.02ms/пост. При 1000 правил = 1ms. Aho-Corasick нужен при 10K+ правил. |

## Что AI понял с первого раза

- Структура: `extract/` пакет, `pipeline.py` — только flow control, бизнес-логика в `extract/*`
- Дедупликация: `UNIQUE(type, value, post_id)` — простой путь без many-to-many миграции
- `yaml.safe_load()` вместо `yaml.load()` — безопасность
- Тесты через `tmp_path` + `monkeypatch.setenv("TH_DB", ...)`

## Где AI упёрся

- **Python 3.9 vs 3.10:** `str | None` — SyntaxError. Нужен `from __future__ import annotations`
- **mypy + yaml:** `Library stubs not installed` → `pip install types-PyYAML`
- **Аннотация глобальной переменной:** `_rules_cache: dict[str, Any] = yaml.safe_load(f)` — SyntaxError (annotated name can't be global). Убрал аннотацию.
- **FK constraint в тестах:** `insert_post(channel_id=1, ...)` до создания канала → IntegrityError. Фикс: сначала `INSERT INTO channels`, потом пост.
- **Склонение в тестах:** `"футболок"` ≠ `"футболки"` (rules.yaml). Тест `test_full_ad` падал. Фикс: использовать именительный падеж.
- **Package-relative путь:** `parent.parent.parent` = `src/`, а `data/` в project root. Нужен 4-й уровень. CWD fallback спасал всё время.

## Что починили в методологии

- **«Теоретическая проблема» ≠ «реальная проблема».** processed_at, process_channel для непарсеных каналов, th reprocess — всё вычеркнуто после доказательства через призму продукта (аудитория, объёмы, приоритет).
- **Package-relative путь:** всегда проверять empirically: `Path(__file__).resolve().parent.parent...` → target. Не считать в уме.
- **Regex `\w` в Python:** по умолчанию Unicode. Для ASCII-only — явные классы `[A-Za-z0-9_]`.

## Что в долгую память

- `\w` в Python regex = Unicode by default. Для ASCII-only использовать `[A-Za-z0-9_]`.
- `from __future__ import annotations` для `X | None` на Python 3.9.
- `yaml.safe_load()` возвращает `Any`, не `dict` — нужен cast или ignore.
- sqlite3 `fetchmany` vs `fetchall`: 50x RAM разница на 100K строк.
- sqlite3 conn-per-post vs batch: 209x разница по времени.
- Package-relative путь: `extract/threadhunter/src/root` = 4 уровня, не 3.

## Отложено

- `th reprocess` — команда для пересчёта тегов без повторного parse.
- Миграция `UNIQUE` для существующих БД (сейчас нет продакшн-БД).
- Aho-Corasick для O(text_length) классификации при росте правил >1000.
- `processed_at` — когда объёмы вырастут до 10K+ постов на канал.
