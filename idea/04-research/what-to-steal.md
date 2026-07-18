[[README|← Назад к Research]]

# What to Steal

## Конкретные решения для проекта пользователя

### 1. Архитектура: Telethon → NLP → SQLite → NocoDB UI

Готовая цепочка из open-source-компонентов, которую можно собрать без переделки ядра:

| Компонент | Репозиторий | Лицензия | Что берём |
|---|---|---|---|
| **Telethon** | github.com/LonamiWebs/Telethon (~8k stars) | MIT | MTProto-клиент для чтения каналов, сообщений, entity |
| **tg-archive** | github.com/knadh/tg-archive (~500 stars) | MIT | Готовый pipeline: скрапинг → SQLite → searchable web UI. Форкнуть и добавить экстракцию контактов |
| **python-phonenumbers** | github.com/daviddrysdale/python-phonenumbers (~4.2k) | Apache-2.0 | Парсинг телефонов из текста, поддержка RU (+7) и KG (+996) |
| **spaCy + ru_core_news_lg** | github.com/explosion/spaCy (~7k stars) | MIT | NER для извлечения ORG, LOC, PERSON из русскоязычного текста |
| **NocoDB** | github.com/nocodb/nocodb (~50k stars) | AGPL-3.0 | UI «умной таблицы» с поиском, фильтрами, тегами. Не писать UI с нуля |

**Что нужно написать самому:**
- Скрипт-оркестратор (join channels → iterate messages → extract → write to DB)
- Логика тегирования (location: Бишкек/Ош/Москва; assortment: одежда/обивка/промтекстиль; business type: фабрика/цех/подрядчик)
- Список ключевых слов для швейной ниши (keyword matching как fallback для NER)

### 2. Chrome-экстеншен как канал дистрибуции

Два Chrome-экстеншена для Telegram-парсинга уже существуют (social-trends.md):
- **Telegram Scraper** (Chrome Web Store) — 1-click парсер каналов/групп по ключевому слову, экспорт в Excel
- **Telegram Group Parser** (by CRMChat) — бесплатный, скрапит списки участников из публичных/приватных групп в CSV

**Что забрать:** модель дистрибуции. Chrome-экстеншен имеет самый низкий порог входа для менеджеров — не нужен Python, не нужен CLI. Для нишевого инструмента (швейные менеджеры в Бишкеке) это критично.

### 3. Конкретные репозитории для форка

| Репозиторий | Зачем форкать | Что изменить |
|---|---|---|
| **tg-archive** (knadh) | Ближайший к готовому продукту: уже архивирует каналы в searchable SQLite с web UI | Добавить экстракцию контактов (телефон/email regex), NER для локаций/компаний, тегирование |
| **TelegramMessageScraper** (willyh101, ~200 stars) | Маленький, делает ровно одно: экспорт сообщений канала в CSV/JSON через Telethon | Добавить enrichment-слой (контакты, теги) |
| **telegram-scraper** (ins0, ~400 stars) | Сканирует группы и каналы, экспорт в JSON. Использует Telethon | Добавить domain-specific парсинг поверх сырых сообщений |
| **Telsca** (JulietKiloCharlie) | Скрапит каналы/группы, извлекает сообщения, инфо о пользователях, медиа | Добавить структурирование по схеме швейной ниши |

### 4. Паттерны из коммерческих продуктов

| У кого | Что забрать |
|---|---|
| **Xreacher** | Full-stack workflow: source → segment → outreach → track. Не просто парсер, а полный цикл |
| **TGCParser** | Модель «опиши аудиторию словами — мы найдём и извлечём». AI-фильтрация по plain-language описанию |
| **CRMChat** | Telegram-native интерфейс. CRM прямо в Telegram, не отдельное веб-приложение |
| **Energent.ai** | No-code воркфлоу + экспорт в дашборды. Мониторинг цен и competitive intelligence |
| **LeadGuru** | Intent-based квалификация: мониторинг ключевых фраз покупки, а не просто парсинг контактов |

### 5. Архитектурные решения от акселераторов

Из accelerators-landscape.md:
- **DryMerge (YC W24):** паттерн «unstructured data in → structured CRM records out» — фреймить как AI-агент, не как парсер
- **Segment (YC S11, exit $3.2B):** data plumbing бизнес может выйти хорошо. Structuring messy data → usable signals — валидная модель
- **LeadGenius (YC S11):** B2B lead data из внешних источников. Но их human-in-the-loop не масштабируется — автоматизация обязательна

## Связанные разделы
- [[../06-architecture/tech-stack|Tech Stack]] — Telethon, python-phonenumbers, spaCy, NocoDB
- [[../06-architecture/agent-loop|Agent Loop]] — как работает pipeline скрапинга
- [[../06-architecture/data-flow|Data Flow]] — поток данных от скрапинга до UI
- [[../06-architecture/memory-model|Memory Model]] — хранение структурированных данных
- [[../06-architecture/permissions|Permissions]] — permission-aware workflows
- [[../06-architecture/triggers|Triggers]] — что запускает скрапинг
- [[../06-architecture/integrations|Integrations]] — внешние системы
