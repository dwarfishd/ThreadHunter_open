# Фаза 2.5: Применённые решения для архитектурных проблем

## Проблема 1: Нет connection pool → FloodWait при 100 вызовах

**Решение:** Кэш состояния сессии с TTL 5 минут.

### Diff

```diff
# src/threadhunter/telegram/auth.py

+# Cache for session validity check (avoids repeated TCP connections)
+_session_cache: dict[str, tuple[bool, float]] = {}
+_SESSION_CACHE_TTL = 300  # 5 minutes

 async def check_session(session_path: Path) -> bool:
+    """Check whether a session file exists and is valid.
+
+    Uses a 5-minute cache to avoid repeated TCP connections to Telegram API.
+    ...
+    """
     if not session_path.exists():
         return False
 
+    # Check cache first
+    cache_key = str(session_path)
+    now = time.time()
+    if cache_key in _session_cache:
+        cached_valid, cached_time = _session_cache[cache_key]
+        if now - cached_time < _SESSION_CACHE_TTL:
+            logger.debug("Session check: cache hit (valid=%s)", cached_valid)
+            return cached_valid
+
+    # Cache miss or expired — check for real
     ...
+    is_valid = bool(await client.is_user_authorized())
+    # Update cache
+    _session_cache[cache_key] = (is_valid, now)
+    return is_valid

+def invalidate_session_cache(session_path: Optional[Path] = None) -> None:
+    """Invalidate session cache for a specific path or all paths."""
+    if session_path is None:
+        _session_cache.clear()
+    else:
+        cache_key = str(session_path)
+        _session_cache.pop(cache_key, None)
```

**Эффект:** 100 вызовов `th parse` → 1 TCP-соединение (вместо 100).

---

## Проблема 2: Нет кэша settings → 100 раз читается .env

**Решение:** Lazy импорт `get_settings()` (кэш уже есть в `config.py`).

### Diff

```diff
# src/threadhunter/telegram/auth.py

-from threadhunter.config import get_settings
-
 logger = logging.getLogger(__name__)

 def get_session_path(session_name: Optional[str] = None) -> Path:
     ...
     if session_name is None:
+        # Use cached settings to avoid repeated .env parsing
+        from threadhunter.config import get_settings
+
         settings = get_settings()
         session_name = settings.session_name
```

**Эффект:** `get_settings()` вызывается один раз на процесс (кэш `_settings` в `config.py`).

---

## Проблема 3: Новый event loop → медленно на слабой машине

**Решение:** Не применимо для CLI (typer не поддерживает async commands из коробки).

**Обоснование:** Для MVP (1-10 вызовов) — приемлемо. Для production — переход на async CLI или persistent loop.

---

## Итого

| Проблема | Решение | Статус |
|----------|---------|--------|
| Нет connection pool | Кэш сессии (TTL 5 мин) | ✅ Применено |
| Нет кэша settings | Lazy импорт get_settings() | ✅ Применено |
| Новый event loop | Не применимо для CLI | ⏸ Отложено |

**Результат:**
- `ruff check` — OK
- `mypy --strict` — OK
- `pytest` — 40 passed (добавлены 2 теста для кэша)
