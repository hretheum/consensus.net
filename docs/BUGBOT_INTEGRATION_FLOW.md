# 🔄 Przepływ Integracji BugBot z Aplikacją

## Jak to działa - krok po kroku

### 1️⃣ Aplikacja generuje błąd

```python
# Użytkownik próbuje pobrać dane
GET /api/users/999

# W kodzie aplikacji:
user = None
return {"name": user.name}  # 💥 AttributeError!
```

### 2️⃣ Middleware łapie błąd i loguje

```python
@app.middleware("http")
async def bugbot_error_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}",
            exc_info=True,
            extra={
                "component": "api",
                "endpoint": str(request.url),
                "client_ip": request.client.host
            }
        )
```

### 3️⃣ Log trafia do pliku

**Plik: `logs/app_errors.log`**
```
2024-01-15 14:23:45 ERROR [myapp] api.py:125 - Unhandled exception in GET /api/users/999
Traceback (most recent call last):
  File "/app/api.py", line 120, in get_user
    return {"name": user.name}
AttributeError: 'NoneType' object has no attribute 'name'
```

### 4️⃣ BugBot skanuje logi

```
BugBot Monitor
     │
     ├─▶ Skanuje: logs/app_errors.log
     │
     ├─▶ Wykrywa pattern: "AttributeError.*NoneType"
     │
     └─▶ Tworzy obiekt Bug
```

### 5️⃣ BugBot analizuje błąd

```python
Bug {
    id: "abc123",
    title: "AttributeError: 'NoneType' object has no attribute 'name'",
    severity: "high",
    category: "runtime",
    component: "api",
    root_cause: "Próba dostępu do atrybutu obiektu None",
    potential_fix: "Sprawdź czy obiekt nie jest None przed dostępem",
    related_files: ["/app/api.py"],
    frequency: 1
}
```

### 6️⃣ BugBot podejmuje akcje

```
┌─────────────────────────────────────┐
│           BugBot Actions            │
├─────────────────────────────────────┤
│                                     │
│  1. Zapisz do bazy błędów          │
│     └─▶ data/bugs.json             │
│                                     │
│  2. Wyślij powiadomienie Slack     │
│     └─▶ #bugs channel              │
│                                     │
│  3. Utwórz GitHub Issue            │
│     └─▶ (jeśli severity=critical)  │
│                                     │
│  4. Zaktualizuj statystyki         │
│     └─▶ API: /api/bugbot/stats     │
│                                     │
└─────────────────────────────────────┘
```

## 📊 Wizualizacja przepływu

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Aplikacja  │────▶│     Logi     │────▶│    BugBot    │
│              │     │              │     │              │
│  try/catch   │     │ app_errors.  │     │  Monitor     │
│  logger.error│     │    .log      │     │  Analyzer    │
│              │     │              │     │  Notifier    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                    ┌─────────────────────────────┼─────────┐
                    │                             │         │
                    ▼                             ▼         ▼
            ┌──────────────┐           ┌──────────────┐  ┌──────────────┐
            │    Slack     │           │    GitHub    │  │   Dashboard  │
            │              │           │              │  │              │
            │  #bugs       │           │  Issues      │  │  Stats API   │
            │  @channel    │           │  Labels      │  │  Charts      │
            └──────────────┘           └──────────────┘  └──────────────┘
```

## 🔍 Przykład rzeczywistego przepływu

### Scenariusz: Błąd płatności w e-commerce

1. **Klient składa zamówienie:**
   ```
   POST /api/orders
   {
     "user_id": 123,
     "items": ["item1", "item2"],
     "payment_method": "card"
   }
   ```

2. **Aplikacja próbuje przetworzyć płatność:**
   ```python
   # Stripe API timeout
   raise Exception("Payment gateway timeout - Stripe API not responding")
   ```

3. **Middleware loguje błąd:**
   ```
   2024-01-15 14:30:12 CRITICAL [myapp] orders.py:89 - Critical error in order processing
   Exception: Payment gateway timeout - Stripe API not responding
   Component: orders
   User ID: 123
   Payment Method: card
   Severity: critical
   ```

4. **BugBot wykrywa i analizuje:**
   - Pattern: "Payment gateway timeout"
   - Severity: CRITICAL (automatyczna eskalacja)
   - Component: payment
   - Root cause: "Timeout połączenia z bramką płatności"

5. **BugBot wykonuje akcje:**
   
   **a) Natychmiastowe powiadomienie Slack:**
   ```
   🔴 [CRITICAL] Payment gateway timeout - Stripe API not responding
   
   Component: payment
   User affected: 123
   Frequency: 3 times in last 5 minutes
   
   Suggested action: Check Stripe status page and implement retry logic
   ```
   
   **b) Tworzy GitHub Issue:**
   ```markdown
   Title: 🔴 [CRITICAL] Payment gateway timeout affecting orders
   
   ## Description
   Multiple payment timeouts detected in production
   
   ## Details
   - First seen: 2024-01-15 14:25:00
   - Occurrences: 3
   - Users affected: 123, 456, 789
   
   ## Suggested Fix
   1. Check Stripe API status
   2. Implement exponential backoff retry
   3. Add circuit breaker pattern
   
   ## Stack Trace
   ```
   
   **c) Email do on-call developer:**
   ```
   Subject: CRITICAL: Payment System Down
   
   Immediate action required!
   3 payment failures in last 5 minutes.
   ```

## 🛠️ Minimalna integracja - 3 kroki

### Krok 1: Dodaj logowanie do aplikacji
```python
import logging
logger = logging.getLogger(__name__)

try:
    # twój kod
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
```

### Krok 2: Skonfiguruj BugBot
```bash
export BUGBOT_LOG_DIRS=/path/to/logs
export BUGBOT_SLACK_WEBHOOK=https://hooks.slack.com/...
```

### Krok 3: Uruchom BugBot
```bash
python src/services/bugbot/run_bugbot.py
```

**To wszystko! BugBot automatycznie:**
- ✅ Skanuje logi co 10 sekund
- ✅ Wykrywa błędy używając regex patterns
- ✅ Analizuje i kategoryzuje
- ✅ Wysyła powiadomienia
- ✅ Tworzy raporty

## 📈 Efekty integracji

Po integracji BugBot dostarczy:

1. **Natychmiastowe alerty** o krytycznych błędach
2. **Automatyczną dokumentację** błędów w GitHub
3. **Statystyki** - które komponenty generują najwięcej błędów
4. **Trendy** - czy liczba błędów rośnie czy maleje
5. **Sugestie napraw** - oszczędność czasu debugowania

## 🎯 Best Practices

1. **Strukturyzuj logi:**
   ```python
   logger.error("msg", extra={"component": "api", "user_id": 123})
   ```

2. **Używaj poziomów:**
   - CRITICAL - wymaga natychmiastowej uwagi
   - ERROR - błąd wpływający na funkcjonalność
   - WARNING - potencjalny problem

3. **Dodawaj kontekst:**
   ```python
   logger.error("Payment failed", exc_info=True, extra={
       "order_id": order_id,
       "amount": amount,
       "payment_method": method
   })
   ```