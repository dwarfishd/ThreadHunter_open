---
name: Architecture reference
description: Навигация по файлам архитектуры ThreadHunter — что где лежит
type: reference
---

Архитектура ThreadHunter разложена по `idea/06-architecture/`:

| Что | Файл |
|---|---|
| Общий обзор архитектуры | `idea/06-architecture/README.md` |
| Схема БД, таблицы, индексы | `idea/06-architecture/memory-model.md` |
| Технологии и зависимости | `idea/06-architecture/tech-stack.md` |
| Поток данных, pipeline | `idea/06-architecture/data-flow.md` |
| Цикл агента (trigger→fetch→AI→store) | `idea/06-architecture/agent-loop.md` |
| Триггеры и расписание | `idea/06-architecture/triggers.md` |
| Интеграции (Telegram, CSV, CRM) | `idea/06-architecture/integrations.md` |
| Права и API-ключи | `idea/06-architecture/permissions.md` |

Дополнительно:
- Концепция и идея: `idea/01-idea/README.md`
- Принцип Local First: `idea/05-principles/local-first.md`
- MVP и первая фича: `idea/09-mvp/one-killer-feature.md`
- Риски и безопасность: `idea/11-risks/`
- Технические планы: `plans/`

**Why:** Быстрый доступ к нужному разделу архитектуры без блуждания по дереву файлов.

**How to apply:** При вопросах по архитектуре сначала искать в соответствующем файле из таблицы. Если файла нет — создавать новый в `idea/06-architecture/`, а не добавлять в README.
