[[README|← Назад к Research]]

# Методологии и архитектурные паттерны

## Что используют конкуренты

| Паттерн | Кто использует | Как применяется | Что стоит взять |
|---|---|---|---|
| **Pipeline-архитектура (scrape → parse → store → search)** | Apify, tg-archive, TGCParser | Последовательный конвейер: сырые сообщения → извлечение сущностей → запись в БД → поиск | Это базовая архитектура. tg-archive уже реализует её до SQLite с веб-интерфейсом |
| **AI-powered parsing (LLM для фильтрации и классификации)** | Tegranium, TGCParser, Energent.ai, Enreach | LLM анализирует текст поста, определяет релевантность, фильтрует спам, классифицирует лиды | AI-фильтрация — ключевое отличие от простого regex-парсинга. Enreach тренировал агента на 30M+ диалогов |
| **Multi-agent / AI agent narrative** | Enreach, DISE CRM, DryMerge (YC W24) | «AI-агент» мониторит каналы, извлекает структурированные записи, обновляет CRM | YC активно финансирует AI-agent нарратив. Фрейминг «агент, а не парсер» важен для инвесторов |
| **Event-driven scraping (24/7 мониторинг)** | TGCParser, LeadGuru, Tegranium | Постоянный мониторинг каналов, фиксация новых сообщений с метаданными автора | Критично для «реальной активности» — статичные профили не дают сигнала, что фабрика сейчас рекламирует |
| **Intent-based qualification** | LeadGuru, Apollo.io, ZoomInfo | Мониторинг сигналов покупки (найм, финансирование, расширение), а не просто извлечение контактов | Интент-сигналы увеличивают конверсию. Для Telegram: мониторинг ключевых фраз «ищем подрядчика», «нужна партия» |
| **Cross-platform outreach** | Xreacher, LeadGuru | Telegram + X/Twitter (+ LinkedIn в разработке) из единого workspace | Если целевая аудитория также активна на других платформах — кросс-платформенность расширяет покрытие |

## Что используют open-source проекты

| Паттерн | Проект | Как применяется |
|---|---|---|
| **MTProto client → message iteration → structured export** | Telethon, Pyrogram, gramjs | Полноценный доступ к Telegram API, итерация по сообщениям, извлечение entity (URL, phone, mention, hashtag) |
| **Regex + NER для извлечения сущностей** | python-phonenumbers, spaCy, Microsoft Presidio | Извлечение телефонов, email, локаций, организаций из свободного текста |
| **SQLite как storage + web UI для поиска** | tg-archive (~500 stars) | Архивирование каналов в searchable SQLite с базовым веб-интерфейсом |
| **Smart spreadsheet как UI** | NocoDB (~50k stars), Directus (~28k stars) | Любой SQL-таблица превращается в searchable, filterable, tag-sortable интерфейс без написания UI |

## Что НЕ используется (и почему это gap)

| Паттерн | Где отсутствует | Почему это важно |
|---|---|---|
| **Domain-specific tagging schema** | Все существующие парсеры | Ни один парсер не применяет тегирование по локации, ассортименту, типу бизнеса. Сырые данные требуют ручной очистки |
| **Russian-language NER** | spaCy имеет модель `ru_core_news_lg`, но конкуренты её не используют | Русскоязычные посты требуют русской NER для извлечения компаний, локаций, категорий продуктов |
| **Vertical-specific structuring** | Все парсеры — general-purpose | Структурирование швейных/производственных лидов (категории: одежда, обивка, промтекстиль) не делается никем |

## Рекомендуемая архитектура

```
Telethon scraper → Python parser → SQLite → NocoDB UI
                   │
             python-phonenumbers
             spaCy NER (ru)
             regex: email, URL
```

**Оценка MVP:** 2-4 недели. Telethon (MIT) + python-phonenumbers (Apache-2.0) + spaCy (MIT) + NocoDB (AGPL-3.0, ок для self-hosted).

## Связанные разделы
- [[../06-architecture/tech-stack|Tech Stack]] — выбранный стек технологий
- [[../06-architecture/agent-loop|Agent Loop]] — pipeline-архитектура
- [[../06-architecture/data-flow|Data Flow]] — поток данных
- [[../07-decisions/tech-decisions|Tech Decisions]] — технические решения
