# Day in the Life

[[02-vision/README|← Назад к Vision]]

**Утро:** Пользователь открывает приложение, видит свежую порцию объявлений, спарсенных за последнюю ночь/неделю.

**Процесс:**
- Система автоматически парсит Telegram-каналы с заданной периодичностью (раз в день, неделю, месяц) — см. [[06-architecture/triggers|Triggers]] и [[05-principles/proactive|Proactive]]
- Собирает: контакты, ассортимент, локацию, текст объявления — см. [[06-architecture/agent-loop|Agent Loop]]
- Сортирует по тегам (локация + что шьют) — см. [[06-architecture/memory-model|Memory Model]]

**Результат:**
- Структурированная база подрядчиков/поставщиков
- Пользователь фильтрует, находит нужные контакты — см. [[05-principles/action-oriented|Action Oriented]]
- Использует данные для:
  - Поиска подрядчиков для тендеров — см. [[03-audience/jobs-to-be-done|Jobs to be Done]]
  - Предложения условий по продвижению поставщикам

## Связанные разделы
- [[02-vision/success-criteria|Success Criteria]]
- [[06-architecture/agent-loop|Agent Loop]]
- [[05-principles/proactive|Proactive]]
- [[09-mvp/scope|MVP Scope]]