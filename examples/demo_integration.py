#!/usr/bin/env python3
"""
Demo: Integracja BugBot z aplikacją w akcji

Ten skrypt pokazuje jak BugBot automatycznie wykrywa i zarządza błędami.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
import aiohttp

# Kolory dla lepszej wizualizacji
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(number, text):
    print(f"{Colors.BLUE}{Colors.BOLD}[Krok {number}]{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

async def check_services():
    """Sprawdza czy usługi działają"""
    print_header("SPRAWDZANIE USŁUG")
    
    services = {
        "Aplikacja": "http://localhost:8001/",
        "BugBot API": "http://localhost:8000/api/bugbot/status"
    }
    
    for name, url in services.items():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    if resp.status == 200:
                        print_success(f"{name} działa na {url}")
                    else:
                        print_error(f"{name} zwrócił status {resp.status}")
        except:
            print_error(f"{name} nie odpowiada na {url}")
            print_info(f"Uruchom: python examples/integration_example_app.py")
            return False
    
    return True

async def demonstrate_integration():
    """Demonstruje integrację BugBot"""
    
    print_header("DEMO: INTEGRACJA BUGBOT Z APLIKACJĄ")
    
    # Krok 1: Sprawdź usługi
    if not await check_services():
        print_error("\nUruchom najpierw aplikację i BugBot!")
        print_info("Terminal 1: python examples/integration_example_app.py")
        print_info("Terminal 2: export BUGBOT_LOG_DIRS=./logs && python src/services/bugbot/run_bugbot.py")
        return
    
    api_url = "http://localhost:8001"
    bugbot_url = "http://localhost:8000/api/bugbot"
    
    async with aiohttp.ClientSession() as session:
        
        # Krok 2: Wyczyść logi
        print_step(1, "Czyszczenie poprzednich błędów...")
        if os.path.exists("logs/app_errors.log"):
            os.remove("logs/app_errors.log")
        print_success("Logi wyczyszczone")
        
        # Krok 3: Generuj różne typy błędów
        print_step(2, "Generowanie błędów testowych...")
        
        errors_to_generate = [
            {
                "name": "NoneType Error",
                "endpoint": "/api/users/999",
                "method": "GET",
                "expected_error": "AttributeError"
            },
            {
                "name": "Timeout Error",
                "endpoint": "/api/users/666",
                "method": "GET",
                "expected_error": "TimeoutError"
            },
            {
                "name": "Validation Error",
                "endpoint": "/api/users/0",
                "method": "GET",
                "expected_error": "ValueError"
            },
            {
                "name": "Payment Error",
                "endpoint": "/api/orders",
                "method": "POST",
                "data": {
                    "user_id": 1,
                    "items": ["item1"],
                    "payment_method": "invalid_method"
                },
                "expected_error": "Invalid payment method"
            }
        ]
        
        for error_config in errors_to_generate:
            print(f"\n  → Generowanie: {error_config['name']}")
            try:
                if error_config['method'] == 'GET':
                    async with session.get(f"{api_url}{error_config['endpoint']}") as resp:
                        print_info(f"    Status: {resp.status}")
                else:
                    async with session.post(
                        f"{api_url}{error_config['endpoint']}", 
                        json=error_config.get('data')
                    ) as resp:
                        print_info(f"    Status: {resp.status}")
            except Exception as e:
                print_error(f"    Błąd połączenia: {e}")
        
        # Krok 4: Wygeneruj błędy przez specjalny endpoint
        print_step(3, "Generowanie dodatkowych błędów...")
        try:
            async with session.post(f"{api_url}/test/generate-errors") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_success(f"Wygenerowano {len(data['errors'])} błędów testowych")
                    for error in data['errors']:
                        print_info(f"  - {error}")
        except Exception as e:
            print_error(f"Nie udało się wygenerować błędów: {e}")
        
        # Krok 5: Czekaj na przetworzenie przez BugBot
        print_step(4, "Czekanie na przetworzenie przez BugBot...")
        for i in range(5, 0, -1):
            print(f"  {i}...", end='', flush=True)
            await asyncio.sleep(1)
        print()
        
        # Krok 6: Pobierz wykryte błędy
        print_step(5, "Sprawdzanie wykrytych błędów...")
        try:
            async with session.get(f"{bugbot_url}/bugs") as resp:
                if resp.status == 200:
                    bugs = await resp.json()
                    print_success(f"BugBot wykrył {len(bugs)} błędów!")
                    
                    print("\n  Wykryte błędy:")
                    for bug in bugs[:10]:  # Pokaż max 10
                        severity_icon = {
                            'critical': '🔴',
                            'high': '🟠',
                            'medium': '🟡',
                            'low': '🟢'
                        }.get(bug['severity'], '⚪')
                        
                        print(f"\n  {severity_icon} [{bug['severity'].upper()}] {bug['title']}")
                        print(f"     Component: {bug['component']}")
                        print(f"     Category: {bug['category']}")
                        print(f"     Frequency: {bug['frequency']}x")
                        print(f"     First seen: {bug['first_seen']}")
        except Exception as e:
            print_error(f"Nie udało się pobrać błędów: {e}")
        
        # Krok 7: Pobierz statystyki
        print_step(6, "Pobieranie statystyk...")
        try:
            async with session.get(f"{bugbot_url}/stats") as resp:
                if resp.status == 200:
                    stats = await resp.json()
                    print_success("Statystyki błędów:")
                    print(f"\n  Łączna liczba: {stats['total_bugs']}")
                    print(f"  Według severity: {stats['by_severity']}")
                    print(f"  Według kategorii: {stats['by_category']}")
                    print(f"  Według komponentu: {stats['by_component']}")
        except Exception as e:
            print_error(f"Nie udało się pobrać statystyk: {e}")
        
        # Krok 8: Symuluj eskalację
        print_step(7, "Symulacja eskalacji błędu...")
        print_info("Generowanie wielokrotnych wystąpień tego samego błędu...")
        
        for i in range(5):
            try:
                async with session.get(f"{api_url}/api/users/999") as resp:
                    pass
            except:
                pass
            await asyncio.sleep(0.5)
        
        print_success("Błąd powinien zostać eskalowany (frequency > 5)")
        
        # Krok 9: Pokaż przykład logów
        print_step(8, "Przykład wygenerowanych logów...")
        if os.path.exists("logs/app_errors.log"):
            with open("logs/app_errors.log", "r") as f:
                lines = f.readlines()[-10:]  # Ostatnie 10 linii
                print("\n  Ostatnie wpisy w logs/app_errors.log:")
                for line in lines:
                    print(f"  {Colors.YELLOW}{line.strip()}{Colors.END}")

async def show_integration_flow():
    """Pokazuje przepływ integracji"""
    print_header("PRZEPŁYW INTEGRACJI BUGBOT")
    
    flow = """
    1. Aplikacja rzuca wyjątek
       ↓
    2. Middleware łapie błąd
       ↓
    3. Logger zapisuje do pliku (logs/app_errors.log)
       ↓
    4. BugBot skanuje plik co 10 sekund
       ↓
    5. BugBot wykrywa wzorzec błędu (regex)
       ↓
    6. BugBot analizuje błąd:
       - Określa severity
       - Identyfikuje komponent
       - Sugeruje rozwiązanie
       ↓
    7. BugBot wykonuje akcje:
       - Zapisuje do bazy
       - Wysyła powiadomienie Slack/Discord
       - Tworzy GitHub Issue (critical)
       - Aktualizuje statystyki
    """
    
    print(flow)
    
    print_info("\nPrzykładowe wzorce wykrywane przez BugBot:")
    patterns = [
        "Traceback.*Exception",
        "ERROR|CRITICAL",
        "AttributeError.*NoneType",
        "TimeoutError|Connection timeout",
        "MemoryError|OutOfMemory",
        "HTTP.*5\\d{2}"
    ]
    for pattern in patterns:
        print(f"  • {pattern}")

async def main():
    """Główna funkcja demo"""
    print(f"\n{Colors.BOLD}BugBot Integration Demo{Colors.END}")
    print("=" * 40)
    
    # Pokaż przepływ
    await show_integration_flow()
    
    # Zapytaj czy kontynuować
    print(f"\n{Colors.YELLOW}Czy chcesz uruchomić demo? [y/n]{Colors.END}")
    choice = input().lower()
    
    if choice == 'y':
        await demonstrate_integration()
        
        print_header("PODSUMOWANIE")
        print("BugBot automatycznie:")
        print_success("Wykrył błędy w aplikacji")
        print_success("Przeanalizował przyczyny")
        print_success("Skategoryzował według severity")
        print_success("Przypisał do komponentów")
        print_success("Zgromadził statystyki")
        
        print(f"\n{Colors.BOLD}Następne kroki:{Colors.END}")
        print("1. Sprawdź API BugBot: http://localhost:8000/api/docs#/bugbot")
        print("2. Zobacz zapisane błędy: cat data/bugs.json | jq")
        print("3. Skonfiguruj powiadomienia (Slack, Discord, Email)")
        print("4. Połącz z GitHub dla automatycznych issues")
    else:
        print("\nDemo anulowane.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo przerwane.{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Błąd: {e}{Colors.END}")