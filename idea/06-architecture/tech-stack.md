[[README|← Назад к Architecture]]

# Tech Stack

## Технологический стек

CLI-утилита + SQLite. Минимум зависимостей, максимум контроля.

## Компоненты

### Парсер (CLI)
- **Язык**: Python 3.10+
- **Telegram API**: Telethon — асинхронная библиотека, MTProto, стабильная, с документацией
- **AI-классификация**: 
  - Локальная LLM (Ollama / llama.cpp) или
  - Лёгкая NER-модель (spaCy + custom pipeline)
  - Решение зависит от качества классификации и ресурсов машины пользователя
- **Расписание**: cron / launchd / Task Scheduler — нативные системные планировщики

### Хранение
- **SQLite** — встраиваемая БД, ноль конфигурации, один файл
- **Миграции**: Alembic или ручные SQL-скрипты
- **Бэкапы**: копирование .db файла

### Интерфейс
- **CLI** — argparse / click / typer
- Команды: `init`, `add-channel`, `parse`, `status`, `export`, `config`

### Зависимости
```
telethon          # Telegram API
sqlite3           # встроено в Python
typer             # CLI framework
pydantic          # валидация конфигов
spacy / ollama    # AI-классификация (опционально)
```

## Почему этот стек

- **Python** — быстрая разработка, богатая экосистема NLP/парсинга
- **SQLite** — один файл, нет сервера, работает везде
- **CLI** — нет GUI-зависимостей, легко автоматизировать, легко тестировать
- **Локальная LLM** — соответствует принципу Local First, нет облачных вызовов
- **Системные планировщики** — не изобретать свой cron, использовать то, что уже есть в ОС

## Альтернативы (рассмотрены, отклонены)

- **Electron GUI** — нарушает Local First (тяжёлый), One Person Company (сложнее поддерживать)
- **Облачная LLM (OpenAI API)** — нарушает Local First, данные уходят наружу
- **PostgreSQL** — требует установки сервера, нарушает принцип «один файл»
- **Node.js** — хуже экосистема для NLP/классификации

## Связанные разделы
- [[../04-research/open-source-landscape|Open-Source Landscape]] — Telethon, spaCy, NocoDB
- [[../07-decisions/tech-decisions|Tech Decisions]] — детальные обоснования решений
- [[../05-principles/local-first|Local First]] — локальная LLM
- [[data-flow|Data Flow]] — как компоненты соединяются
- [[memory-model|Memory Model]] — SQLite схема
