[[README|← Назад к Architecture]]

# Memory Model

## Хранение данных

Все данные хранятся локально в SQLite. Нет облачной синхронизации, нет мульти-юзера. Один пользователь — одна база.

## Схема базы данных

### Таблица: `channels`
| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | ID канала |
| `telegram_id` | TEXT UNIQUE | Telegram channel ID/username |
| `name` | TEXT | Название канала |
| `added_at` | DATETIME | Дата добавления |
| `last_parsed` | DATETIME | Дата последнего парсинга |

### Таблица: `posts`
| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | ID поста |
| `channel_id` | INTEGER FK → channels | Источник |
| `telegram_post_id` | TEXT UNIQUE | ID поста в Telegram |
| `raw_text` | TEXT | Исходный текст |
| `published_at` | DATETIME | Дата публикации в канале |
| `parsed_at` | DATETIME | Дата парсинга |
| `has_photo` | BOOLEAN | Есть ли фото/вложение |
| `status` | TEXT | active / closed |

### Таблица: `contacts`
| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | ID контакта |
| `post_id` | INTEGER FK → posts | Связанный пост |
| `type` | TEXT | phone / telegram / email / name |
| `value` | TEXT | Значение контакта |

### Таблица: `tags`
| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | ID тега |
| `post_id` | INTEGER FK → posts | Связанный пост |
| `type` | TEXT | location / assortment / offer_type |
| `value` | TEXT | Значение тега (напр. "Бишкек", "куртки", "ищут подрядчика") |

## Принципы хранения

- **Нет soft-delete** — если пост удалён из канала, он остаётся в базе с `status = closed`
- **Дедупликация по `telegram_post_id`** — один пост = одна запись, повторные пропуски игнорируются
- **Бэкапы** — экспорт SQLite-файла, не облачный sync
- **Нет шифрования** — данные локальные, пользователь сам защищает свою машину
- **Индексы** — на `telegram_post_id`, `tags.value`, `contacts.value`, `posts.published_at` для быстрого поиска

## Связанные разделы
- [[../05-principles/local-first|Local First]] — данные локально, SQLite
- [[../07-decisions/tech-decisions|Tech Decisions]] — SQLite, Alembic
- [[../09-mvp/scope|Scope]] — собираемые поля в MVP
- [[data-flow|Data Flow]] — как данные записываются в SQLite
