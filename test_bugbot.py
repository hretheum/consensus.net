#!/usr/bin/env python3
"""
Test script dla BugBot - demonstracja działania
"""

import os
import asyncio
import logging
from datetime import datetime


async def generate_test_logs():
    """Generuje przykładowe logi z błędami do testowania BugBot"""
    
    # Utwórz katalog logs jeśli nie istnieje
    os.makedirs("logs", exist_ok=True)
    
    # Przykładowe błędy do wygenerowania
    test_errors = [
        {
            "type": "exception",
            "content": """2024-01-15 10:23:45 ERROR: Failed to process user request
Traceback (most recent call last):
  File "/app/src/api/endpoints/users.py", line 45, in get_user
    user = await db.get_user(user_id)
  File "/app/src/services/database.py", line 123, in get_user
    result = await self.query(f"SELECT * FROM users WHERE id = {user_id}")
AttributeError: 'NoneType' object has no attribute 'query'
"""
        },
        {
            "type": "timeout",
            "content": """2024-01-15 10:25:12 ERROR: Database connection timeout
TimeoutError: Connection to database timed out after 30 seconds
  Host: db.example.com:5432
  Database: production
  User: app_user
"""
        },
        {
            "type": "memory",
            "content": """2024-01-15 10:26:33 CRITICAL: Memory allocation failed
MemoryError: Unable to allocate 2.5GB for cache buffer
Current memory usage: 7.8GB / 8GB
Heap exhausted, consider increasing memory limits
"""
        },
        {
            "type": "permission",
            "content": """2024-01-15 10:27:45 ERROR: File access denied
PermissionError: [Errno 13] Permission denied: '/var/log/app/debug.log'
User 'www-data' does not have write permissions
"""
        },
        {
            "type": "http_500",
            "content": """2024-01-15 10:28:55 ERROR: API request failed
HTTP 500 Internal Server Error
Endpoint: /api/v1/process-payment
Response: {"error": "Payment gateway unavailable"}
"""
        },
        {
            "type": "null_pointer",
            "content": """2024-01-15 10:30:02 ERROR: Null pointer exception in auth service
TypeError: Cannot read property 'id' of None
  at AuthService.validateToken (/app/src/services/auth.py:78)
  at middleware.authenticate (/app/src/api/middleware.py:34)
User token validation failed
"""
        }
    ]
    
    # Zapisz błędy do pliku logu
    log_file = "logs/application.log"
    
    print(f"🔄 Generowanie testowych logów w {log_file}...")
    
    with open(log_file, "a") as f:
        for i, error in enumerate(test_errors):
            f.write(f"\n{error['content']}\n")
            print(f"  ✓ Dodano błąd typu: {error['type']}")
            
            # Czekaj chwilę między błędami
            await asyncio.sleep(1)
    
    print(f"✅ Wygenerowano {len(test_errors)} testowych błędów")
    

async def test_bugbot_api():
    """Testuje API BugBot"""
    import aiohttp
    
    api_url = "http://localhost:8000/api/bugbot"
    
    print("\n🧪 Testowanie API BugBot...")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Sprawdź status
        print("\n1️⃣ Sprawdzanie statusu BugBot...")
        try:
            async with session.get(f"{api_url}/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"  ✓ BugBot działa: {data['running']}")
                    print(f"  ✓ Liczba błędów: {data['bugs_count']}")
                    print(f"  ✓ Monitorowane pliki: {data['monitored_files']}")
                else:
                    print(f"  ✗ Błąd: {resp.status}")
        except Exception as e:
            print(f"  ✗ Nie można połączyć z API: {e}")
            
        # Test 2: Wymuszenie skanowania
        print("\n2️⃣ Wymuszanie skanowania...")
        try:
            async with session.post(f"{api_url}/scan") as resp:
                if resp.status == 200:
                    print("  ✓ Skanowanie uruchomione")
                else:
                    print(f"  ✗ Błąd: {resp.status}")
        except Exception as e:
            print(f"  ✗ Błąd: {e}")
            
        # Czekaj na przetworzenie
        await asyncio.sleep(3)
        
        # Test 3: Pobierz wykryte błędy
        print("\n3️⃣ Pobieranie wykrytych błędów...")
        try:
            async with session.get(f"{api_url}/bugs") as resp:
                if resp.status == 200:
                    bugs = await resp.json()
                    print(f"  ✓ Wykryto {len(bugs)} błędów:")
                    for bug in bugs[:5]:  # Pokaż pierwsze 5
                        print(f"    • [{bug['severity']}] {bug['title']}")
                        print(f"      Komponent: {bug['component']}, Częstotliwość: {bug['frequency']}")
                else:
                    print(f"  ✗ Błąd: {resp.status}")
        except Exception as e:
            print(f"  ✗ Błąd: {e}")
            
        # Test 4: Pobierz statystyki
        print("\n4️⃣ Pobieranie statystyk...")
        try:
            async with session.get(f"{api_url}/stats") as resp:
                if resp.status == 200:
                    stats = await resp.json()
                    print("  ✓ Statystyki błędów:")
                    print(f"    • Łącznie: {stats['total_bugs']}")
                    print(f"    • Według severity: {stats['by_severity']}")
                    print(f"    • Według kategorii: {stats['by_category']}")
                else:
                    print(f"  ✗ Błąd: {resp.status}")
        except Exception as e:
            print(f"  ✗ Błąd: {e}")


async def main():
    """Główna funkcja testowa"""
    print("🐛 BugBot - Test demonstracyjny")
    print("================================\n")
    
    # Krok 1: Generuj testowe logi
    await generate_test_logs()
    
    # Krok 2: Testuj API (jeśli działa)
    print("\n⏳ Czekam 5 sekund na przetworzenie logów przez BugBot...")
    await asyncio.sleep(5)
    
    await test_bugbot_api()
    
    print("\n✅ Test zakończony!")
    print("\n💡 Wskazówki:")
    print("  • Uruchom BugBot: python src/services/bugbot/run_bugbot.py")
    print("  • Uruchom API: python src/main.py")
    print("  • Sprawdź dokumentację API: http://localhost:8000/api/docs#/bugbot")
    print("  • Skonfiguruj powiadomienia w zmiennych środowiskowych (BUGBOT_*)")


if __name__ == "__main__":
    # Konfiguracja loggera
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Uruchom test
    asyncio.run(main())