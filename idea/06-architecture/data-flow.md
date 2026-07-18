[[README|← Назад к Architecture]]

# Data Flow

## Поток данных

От Telegram-канала до структурированной записи в SQLite.

## Pipeline

```
Telegram Channel
       │
       ▼
┌─────────────────┐
│   Fetch Post    │  Telethon: получение поста, текста, метаданных
└────────┬────────┘
         │ raw_text, post_id, published_at, media_info
         ▼
┌─────────────────┐
│   Extract       │  Regex + NLP: извлечение контактов (телефон, username, email)
│   Contacts      │
└────────┬────────┘
         │ contacts[]
         ▼
┌─────────────────┐
│   AI Classify   │  Локальная LLM / spaCy: определение тегов
│   Tags          │  - location (город, регион)
│                 │  - assortment (что шьют)
│                 │  - offer_type (ищут/предлагают)
└────────┬────────┘
         │ tags[]
         ▼
┌─────────────────┐
│   Deduplicate   │  Проверка по telegram_post_id — пропуск если уже в базе
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Store SQLite  │  Запись в posts, contacts, tags
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Notify?       │  Если есть новые релевантные объявления — уведомление
└─────────────────┘
```

## Форматы данных

### Вход (из Telegram)
```json
{
  "channel_id": "@shвейные_канал",
  "post_id": 12345,
  "text": "Ищем швейное производство в Бишкеке...\nКонтакт: +996 555 123456\n",
  "published_at": "2026-06-30T10:00:00Z",
  "has_photo": true
}
```

### Промежуточный (после extraction)
```json
{
  "contacts": [
    {"type": "phone", "value": "+996 555 123456"}
  ]
}
```

### Промежуточный (после classification)
```json
{
  "tags": [
    {"type": "location", "value": "Бишкек"},
    {"type": "offer_type", "value": "ищут подрядчика"}
  ]
}
```

### Выход (в SQLite)
- `posts` — 1 запись
- `contacts` — N записей (по одному на контакт)
- `tags` — M записей (по одному на тег)

## Обработка ошибок

| Ошибка | Действие |
|---|---|
| Telegram API недоступен | Retry через 1 час, макс. 3 раза |
| Post не содержит контактов | Сохранить пост, пометить `contacts_count = 0` |
| AI-классификация не уверена | Сохранить с `confidence < threshold`, пометить для ручной проверки |
| Дубликат post_id | Пропустить, залогировать |
| SQLite locked | Retry через 5 секунд |

## Связанные разделы
- [[agent-loop|Agent Loop]] — полный цикл обработки
- [[tech-stack|Tech Stack]] — компоненты pipeline
- [[memory-model|Memory Model]] — схема SQLite
- [[triggers|Triggers]] — что запускает pipeline
