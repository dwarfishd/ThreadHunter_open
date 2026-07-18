# 06 — Architecture

[[idea/README|← Назад к Idea Canvas]]

## Архитектура продукта

CLI-утилита на Python + SQLite. Локальный парсинг Telegram с AI-классификацией.

- [[06-architecture/agent-loop|agent-loop]] — Цикл: scheduled trigger → fetch → extract → AI classify → store → notify
- [[06-architecture/memory-model|memory-model]] — SQLite: channels, posts, contacts, tags. Один файл, ноль серверов.
- [[06-architecture/permissions|permissions]] — Локальные API-ключи пользователя + session file. Продукт только читает.
- [[06-architecture/triggers|triggers]] — Cron/launchd/Task Scheduler. Daily (default), weekly, monthly. + manual override.
- [[06-architecture/integrations|integrations]] — MVP: Telegram API. Future: CSV/Excel export, CRM.
- [[06-architecture/tech-stack|tech-stack]] — Python + Telethon + SQLite + локальная LLM/spaCy. CLI через Typer.
- [[06-architecture/data-flow|data-flow]] — Pipeline от Telegram-поста до записи в SQLite с дедупликацией и обработкой ошибок.

## Связанные разделы
- [[04-research/what-to-steal|What to Steal]] — что взять из open-source
- [[05-principles/local-first|Local First]] — принцип, определяющий архитектуру
- [[07-decisions/tech-decisions|Tech Decisions]]
