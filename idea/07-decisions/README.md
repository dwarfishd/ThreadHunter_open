# 07 — Decisions

[[idea/README|← Назад к Idea Canvas]]

## Ключевые решения и компромиссы

### Технические ([[07-decisions/tech-decisions|tech-decisions]])
- Python + Telethon для Telegram API
- Локальная LLM (Ollama/llama.cpp) для классификации
- SQLite + Alembic для хранения и миграций
- Typer для CLI
- Системные планировщики (cron/launchd/Task Scheduler)

### Продуктовые ([[07-decisions/product-decisions|product-decisions]])
- Сохранять посты даже без контактов (собираем всё, фильтруем потом)
- CLI, не GUI (скорость разработки > красивый интерфейс)
- Парсинг по расписанию (Proactive)
- Один пользователь, одна база (One Person Company)
- 3 типа тегов в MVP: локация, ассортимент, тип предложения
- CSV экспорт — первая интеграция, не CRM API

### Компромиссы ([[07-decisions/trade-offs|trade-offs]])
- Локальная LLM ↔ качество классификации
- CLI ↔ доступность для не-технических пользователей
- SQLite ↔ масштабируемость
- Сохранять всё ↔ чистота данных
- Только чтение ↔ функциональность
- Один пользователь ↔ TAM

## Связанные разделы
- [[06-architecture/README|Архитектура]] — решения определяют архитектуру
- [[05-principles/README|Принципы]] — каждое решение привязано к принципу
- [[07-decisions/trade-offs|Trade-offs]]
