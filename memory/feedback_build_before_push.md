---
name: Build before push
description: Перед git push — npm run build, не только tsc
type: feedback
---

Перед `git push` обязательно запускать `npm run build`, а не только `tsc`.

**Why:** `tsc` проверяет типы, но `npm run build` выполняет полный цикл — линтинг, сборку, тесты. Только typescript-проверка не ловит все проблемы.

**How to apply:** После завершения фичи и перед коммитом/пушем всегда запускать `npm run build` как финальную проверку. Если проект использует другую систему сборки — применять её аналог.
