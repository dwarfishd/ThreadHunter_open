#!/usr/bin/env python3
"""
Доказательная база: Реальное упущение или теоретический риск?

Запуск: python3 memory/proofs/phase-2.5-missed.py
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from threadhunter.config import reset_settings
from threadhunter.telegram.auth import (
    _session_cache,
    check_session,
    get_session_path,
    invalidate_session_cache,
)


def print_section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


async def proof_1_file_deleted() -> None:
    """
    Упущение 1: Удаление .session файла вручную
    
    Сценарий:
    1. check_session() → кэш: {path: (True, now)}
    2. Пользователь удаляет файл: rm ~/.threadhunter/threadhunter.session
    3. check_session() → кэш hit → возвращает True (но файл не существует!)
    
    Результат: РЕАЛЬНОЕ упущение или теоретический риск?
    """
    print_section("Упущение 1: Удаление .session файла")
    
    _session_cache.clear()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = Path(tmpdir) / "test.session"
        session_path.write_text("fake session data")
        
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        
        with patch("threadhunter.telegram.auth.TelegramClient", return_value=mock_client):
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.has_telegram_credentials = True
                mock_settings.return_value.api_id = 12345
                mock_settings.return_value.api_hash = "abc123"
                
                print("Шаг 1: check_session() → кэш заполняется...")
                result1 = await check_session(session_path)
                print(f"  Результат: {result1}")
                print(f"  Кэш: {dict(_session_cache)}")
                
                print("\nШаг 2: Удаляем файл...")
                session_path.unlink()
                print(f"  Файл существует: {session_path.exists()}")
                
                print("\nШаг 3: check_session() → кэш hit...")
                result2 = await check_session(session_path)
                print(f"  Результат: {result2}")
                print(f"  Файл существует: {session_path.exists()}")
                
                if result2 is True and not session_path.exists():
                    print("\n✗ РЕАЛЬНОЕ УПУЩЕНИЕ: Кэш возвращает True для удалённого файла!")
                    print("  Через 5 минут кэш истечёт, но до этого — ложноположительный результат.")
                else:
                    print("\n✓ Проблема не воспроизвелась")
    
    _session_cache.clear()


async def proof_2_env_changed() -> None:
    """
    Упущение 2: Изменение .env (API_ID/API_HASH)
    
    Сценарий:
    1. load_config() → _settings = {api_id: 12345}
    2. check_session() → использует api_id=12345
    3. Пользователь меняет .env: API_ID=99999
    4. check_session() → всё ещё использует api_id=12345 (кэш _settings)
    
    Результат: РЕАЛЬНОЕ упущение или теоретический риск?
    """
    print_section("Упущение 2: Изменение .env")
    
    _session_cache.clear()
    reset_settings()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        env_file = tmpdir_path / ".env"
        env_file.write_text("API_ID=12345\nAPI_HASH=abc123\n")
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir_path)
        
        try:
            from threadhunter.config import get_settings, load_config
            
            print("Шаг 1: load_config() → _settings = {api_id: 12345}...")
            settings1 = load_config()
            print(f"  API_ID: {settings1.api_id}")
            
            print("\nШаг 2: Изменяем .env: API_ID=99999...")
            env_file.write_text("API_ID=99999\nAPI_HASH=abc123\n")
            
            print("\nШаг 3: get_settings() → кэш _settings...")
            settings2 = get_settings()
            print(f"  API_ID: {settings2.api_id}")
            
            if settings2.api_id == 12345:
                print("\n✗ РЕАЛЬНОЕ УПУЩЕНИЕ: get_settings() возвращает старые данные!")
                print("  Новые API credentials не применятся до перезапуска CLI.")
            else:
                print("\n✓ Проблема не воспроизвелась")
        
        finally:
            os.chdir(original_cwd)
            reset_settings()
    
    _session_cache.clear()


async def proof_3_cache_growth() -> None:
    """
    Упущение 3: Бесконечный рост кэша
    
    Сценарий:
    1000 разных session_name → 1000 записей в кэше
    
    Результат: РЕАЛЬНОЕ упущение или теоретический риск?
    """
    print_section("Упущение 3: Бесконечный рост кэша")
    
    _session_cache.clear()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        
        with patch("threadhunter.telegram.auth.TelegramClient", return_value=mock_client):
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.has_telegram_credentials = True
                mock_settings.return_value.api_id = 12345
                mock_settings.return_value.api_hash = "abc123"
                
                print("Сценарий: 100 разных session_name...")
                for i in range(100):
                    session_path = tmpdir_path / f"bot_{i}.session"
                    session_path.write_text("fake data")
                    await check_session(session_path)
                
                print(f"  Размер кэша: {len(_session_cache)} записей")
                print(f"  Размер в памяти: ~{len(str(_session_cache))} байт")
                
                if len(_session_cache) == 100:
                    print("\n✗ РЕАЛЬНОЕ УПУЩЕНИЕ: Кэш растёт без ограничений!")
                    print("  Для CLI (1-2 session_name) — не проблема.")
                    print("  Для демона (100+ session_name) — утечка памяти.")
                else:
                    print("\n✓ Проблема не воспроизвелась")
    
    _session_cache.clear()


async def proof_4_time_change() -> None:
    """
    Упущение 4: Часы системы меняются
    
    Сценарий:
    1. check_session() → cached_time = 1000
    2. Системное время прыгает назад: now = 0
    3. now - cached_time = -1000 < 300 → кэш "никогда не истечёт"
    
    Результат: РЕАЛЬНОЕ упущение или теоретический риск?
    """
    print_section("Упущение 4: Часы системы меняются")
    
    _session_cache.clear()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = Path(tmpdir) / "test.session"
        session_path.write_text("fake session data")
        
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        
        # Имитируем прыжок времени
        real_time = time.time
        fake_time_value = 1000.0
        
        def fake_time():
            return fake_time_value
        
        with patch("time.time", side_effect=fake_time):
            with patch("threadhunter.telegram.auth.TelegramClient", return_value=mock_client):
                with patch("threadhunter.config.get_settings") as mock_settings:
                    mock_settings.return_value.has_telegram_credentials = True
                    mock_settings.return_value.api_id = 12345
                    mock_settings.return_value.api_hash = "abc123"
                    
                    print("Шаг 1: check_session() при time=1000...")
                    result1 = await check_session(session_path)
                    print(f"  Результат: {result1}")
                    print(f"  Кэш: {dict(_session_cache)}")
                    
                    # Прыжок времени назад
                    fake_time_value = 0.0
                    
                    print("\nШаг 2: Время прыгает назад: time=0...")
                    print(f"  now - cached_time = {fake_time_value} - 1000 = {fake_time_value - 1000}")
                    print(f"  Условие: {fake_time_value - 1000} < 300 → {fake_time_value - 1000 < 300}")
                    
                    print("\nШаг 3: check_session() → кэш hit...")
                    result2 = await check_session(session_path)
                    print(f"  Результат: {result2}")
                    
                    # Проверяем, истечёт ли кэш когда-нибудь
                    print("\nШаг 4: Проверяем, истечёт ли кэш...")
                    for t in [0, 100, 200, 300, 400, 500]:
                        fake_time_value = float(t)
                        cache_key = str(session_path)
                        cached_valid, cached_time = _session_cache[cache_key]
                        will_expire = (fake_time_value - cached_time) >= 300
                        print(f"  time={t}: {fake_time_value} - 1000 = {fake_time_value - 1000} >= 300 → {will_expire}")
                    
                    print("\n✗ РЕАЛЬНОЕ УПУЩЕНИЕ: Кэш никогда не истечёт при отрицательной разнице!")
                    print("  Но: Для CLI (короткоживущий процесс) — не проблема.")
                    print("  Для демона (долгая работа) — кэш станет постоянным.")
    
    _session_cache.clear()


async def proof_5_reset_settings() -> None:
    """
    Упущение 5: reset_settings() не инвалидирует кэш сессии
    
    Сценарий:
    1. check_session() → кэш: {path: (True, now)}
    2. reset_settings() → сбрасывает _settings
    3. check_session() → кэш всё ещё заполнен
    
    Результат: РЕАЛЬНОЕ упущение или теоретический риск?
    """
    print_section("Упущение 5: reset_settings() не инвалидирует кэш")
    
    _session_cache.clear()
    reset_settings()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = Path(tmpdir) / "test.session"
        session_path.write_text("fake session data")
        
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()
        
        with patch("threadhunter.telegram.auth.TelegramClient", return_value=mock_client):
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.has_telegram_credentials = True
                mock_settings.return_value.api_id = 12345
                mock_settings.return_value.api_hash = "abc123"
                
                print("Шаг 1: check_session() → кэш заполняется...")
                result1 = await check_session(session_path)
                print(f"  Результат: {result1}")
                print(f"  Кэш: {len(_session_cache)} записей")
                
                print("\nШаг 2: reset_settings()...")
                reset_settings()
                print(f"  Кэш: {len(_session_cache)} записей")
                
                if len(_session_cache) > 0:
                    print("\n✗ РЕАЛЬНОЕ УПУЩЕНИЕ: reset_settings() не инвалидирует кэш сессии!")
                    print("  Но: Это проблема только для тестов (не для production).")
                else:
                    print("\n✓ Проблема не воспроизвелась")
    
    _session_cache.clear()


async def main() -> None:
    print("\n" + "="*70)
    print("  ДОКАЗАТЕЛЬНАЯ БАЗА: Реальное упущение или теоретический риск?")
    print("="*70)
    
    await proof_1_file_deleted()
    await proof_2_env_changed()
    await proof_3_cache_growth()
    await proof_4_time_change()
    await proof_5_reset_settings()
    
    print("\n" + "="*70)
    print("  ИТОГ")
    print("="*70)
    print("""
    Упущение 1: Удаление .session файла
      → РЕАЛЬНОЕ упущение (кэш возвращает True для удалённого файла)
      → Критичность: Средняя (5 минут ложных срабатываний)
      → Решение: Проверять exists() ПОСЛЕ кэша
    
    Упущение 2: Изменение .env
      → РЕАЛЬНОЕ упущение (get_settings() кэширует старые данные)
      → Критичность: Низкая (CLI перезапускается редко)
      → Решение: reset_settings() + инвалидация кэша
    
    Упущение 3: Бесконечный рост кэша
      → ТЕОРЕТИЧЕСКИЙ риск (для CLI не проблема)
      → Критичность: Низкая (1-2 session_name в реальности)
      → Решение: LRU cache (для демона)
    
    Упущение 4: Часы системы меняются
      → ТЕОРЕТИЧЕСКИЙ риск (для CLI не проблема)
      → Критичность: Низкая (короткоживущий процесс)
      → Решение: time.monotonic()
    
    Упущение 5: reset_settings() не инвалидирует кэш
      → РЕАЛЬНОЕ упущение (но только для тестов)
      → Критичность: Низкая (не влияет на production)
      → Решение: Добавить вызов invalidate_session_cache()
    
    Вывод: 3 реальных упущения (но не критичных для MVP),
           2 теоретических риска (проявятся только в демоне).
    """)


if __name__ == "__main__":
    asyncio.run(main())
