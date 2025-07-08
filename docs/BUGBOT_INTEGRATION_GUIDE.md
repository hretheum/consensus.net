# 🔌 Przewodnik Integracji BugBot

## Spis treści

1. [Przegląd metod integracji](#przegląd-metod-integracji)
2. [Integracja przez pliki logów](#1-integracja-przez-pliki-logów)
3. [Integracja przez API](#2-integracja-przez-api)
4. [Integracja Docker/Kubernetes](#3-integracja-dockerkubernetes)
5. [Integracja z frameworkami](#4-integracja-z-frameworkami)
6. [Najlepsze praktyki](#najlepsze-praktyki)

## Przegląd metod integracji

BugBot można zintegrować z aplikacjami na kilka sposobów:

| Metoda | Złożoność | Zalety | Wady |
|--------|-----------|--------|------|
| **Pliki logów** | ⭐ Niska | Prosta, nie wymaga zmian w kodzie | Opóźnienie w wykrywaniu |
| **API** | ⭐⭐ Średnia | Natychmiastowe raportowanie | Wymaga zmian w kodzie |
| **Docker** | ⭐⭐ Średnia | Izolacja, łatwe skalowanie | Wymaga konteneryzacji |
| **Kubernetes** | ⭐⭐⭐ Wysoka | Pełna automatyzacja | Złożona konfiguracja |
| **Middleware** | ⭐⭐ Średnia | Automatyczne przechwytywanie | Specyficzne dla frameworka |

## 1. Integracja przez pliki logów

### 🟢 Najprostsza metoda - BugBot skanuje pliki logów aplikacji

#### Krok 1: Skonfiguruj logowanie w aplikacji

```python
import logging
import logging.handlers

# Konfiguracja podstawowa
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s [%(name)s] %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)
```

#### Krok 2: Uruchom BugBot wskazując katalog logów

```bash
export BUGBOT_LOG_DIRS=/path/to/your/logs
python src/services/bugbot/run_bugbot.py
```

#### Przykłady dla różnych języków:

**Python:**
```python
logger = logging.getLogger(__name__)
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
```

**Node.js (Winston):**
```javascript
const winston = require('winston');
const logger = winston.createLogger({
  level: 'error',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' })
  ]
});

try {
  riskyOperation();
} catch (error) {
  logger.error('Operation failed', { error: error.message, stack: error.stack });
}
```

**Java (Log4j2):**
```java
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

private static final Logger logger = LogManager.getLogger(MyClass.class);

try {
    riskyOperation();
} catch (Exception e) {
    logger.error("Operation failed", e);
}
```

## 2. Integracja przez API

### 🟡 Średnio zaawansowana - aplikacja komunikuje się z BugBot API

#### Klient API

```python
class BugBotAPIClient:
    def __init__(self, base_url="http://localhost:8000/api/bugbot"):
        self.base_url = base_url
        
    async def report_error(self, error_data):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/report", json=error_data) as resp:
                return resp.status == 200
```

#### Middleware automatycznego raportowania

```python
# FastAPI
class BugBotMiddleware:
    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            await self.report_to_bugbot({
                "endpoint": str(request.url),
                "method": request.method,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise

app.add_middleware(BugBotMiddleware)
```

#### Dekorator dla funkcji

```python
@bugbot_monitor(component="payment", severity="critical")
async def process_payment(amount: float):
    # Automatyczne monitorowanie błędów
    if amount <= 0:
        raise ValueError("Invalid amount")
```

## 3. Integracja Docker/Kubernetes

### 🔴 Zaawansowana - BugBot jako część infrastruktury

#### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    volumes:
      - ./logs:/app/logs
    depends_on:
      - bugbot
      
  bugbot:
    image: bugbot:latest
    volumes:
      - ./logs:/app/logs:ro
    environment:
      - BUGBOT_LOG_DIRS=/app/logs
      - BUGBOT_SLACK_WEBHOOK=${SLACK_WEBHOOK}
```

#### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bugbot
spec:
  template:
    spec:
      containers:
      - name: bugbot
        image: bugbot:latest
        volumeMounts:
        - name: app-logs
          mountPath: /logs
          readOnly: true
```

#### Sidecar Pattern

```yaml
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: shared-logs
      mountPath: /app/logs
      
  - name: bugbot-sidecar
    image: bugbot:latest
    volumeMounts:
    - name: shared-logs
      mountPath: /logs
      readOnly: true
```

## 4. Integracja z frameworkami

### Django

```python
# settings.py
MIDDLEWARE = [
    'myapp.middleware.BugBotErrorMiddleware',
    # ...
]

LOGGING = {
    'handlers': {
        'bugbot': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/logs/django_errors.log',
        }
    }
}
```

### Flask

```python
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled: {e}", exc_info=True)
    return {"error": "Internal error"}, 500
```

### Spring Boot

```yaml
# application.yml
logging:
  level:
    root: ERROR
  file:
    name: logs/spring-app.log
  pattern:
    file: "%d{yyyy-MM-dd HH:mm:ss} %-5level [%thread] %logger{36} - %msg%n"
```

### Express.js

```javascript
app.use((err, req, res, next) => {
  logger.error({
    error: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method
  });
  res.status(500).json({ error: 'Internal error' });
});
```

## 5. Integracja z narzędziami monitoringu

### Sentry + BugBot

```python
sentry_sdk.init(
    before_send=lambda event, hint: log_to_bugbot(event)
)
```

### Prometheus + BugBot

```python
error_counter = Counter('app_errors', 'Total errors', ['type'])

def track_error(error_type):
    error_counter.labels(type=error_type).inc()
    logger.error(f"Error tracked: {error_type}")
```

### ELK Stack + BugBot

```yaml
# logstash.conf
filter {
  if [level] == "ERROR" {
    mutate {
      add_tag => ["bugbot"]
    }
  }
}
```

## Najlepsze praktyki

### 1. Strukturyzuj logi

```python
logger.error(
    "Payment failed",
    extra={
        'component': 'payment',
        'user_id': user_id,
        'amount': amount,
        'error_code': 'PAY_001'
    }
)
```

### 2. Używaj poziomów logowania

- **CRITICAL**: Krytyczne błędy wymagające natychmiastowej uwagi
- **ERROR**: Błędy wpływające na funkcjonalność
- **WARNING**: Ostrzeżenia o potencjalnych problemach

### 3. Dodawaj kontekst

```python
try:
    process_order(order_id)
except Exception as e:
    logger.error(
        f"Order processing failed",
        exc_info=True,
        extra={
            'order_id': order_id,
            'customer_id': customer_id,
            'total_amount': total,
            'items_count': len(items)
        }
    )
```

### 4. Rate limiting

Unikaj spamowania logów:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1000)
def should_log_error(error_key: str, window: int = 300):
    # Log każdy unikalny błąd tylko raz na 5 minut
    return True

if should_log_error(str(error)[:50]):
    logger.error(f"Rate limited error: {error}")
```

### 5. Środowiskowe zmienne

```bash
# .env
BUGBOT_LOG_LEVEL=ERROR
BUGBOT_LOG_DIRS=/app/logs,/var/log/myapp
BUGBOT_SCAN_INTERVAL=30
BUGBOT_SLACK_WEBHOOK=https://hooks.slack.com/...
```

### 6. Testowanie integracji

```python
# test_bugbot_integration.py
def test_error_logging():
    with open('logs/test.log', 'w') as f:
        f.write('ERROR: Test error for BugBot\n')
    
    # Sprawdź czy BugBot wykrył błąd
    response = requests.get('http://localhost:8000/api/bugbot/bugs')
    assert response.status_code == 200
    assert len(response.json()) > 0
```

## Przykład pełnej integracji

```python
# app.py
import logging
from bugbot_client import BugBotClient

# Konfiguracja
logging.basicConfig(
    level=logging.ERROR,
    handlers=[
        logging.FileHandler('logs/app.log'),
        BugBotHandler()  # Custom handler
    ]
)

# Middleware
app.add_middleware(BugBotMiddleware)

# Error handlers
@app.exception_handler(Exception)
async def bugbot_exception_handler(request, exc):
    logger.error(f"Unhandled exception", exc_info=True)
    return JSONResponse({"error": "Internal error"}, 500)

# Monitoring decorator
@bugbot_monitor(component="api", severity="high")
async def api_endpoint():
    # Twój kod
    pass
```

## Troubleshooting

### BugBot nie wykrywa błędów

1. Sprawdź czy pliki logów są tworzone
2. Sprawdź uprawnienia do odczytu
3. Zweryfikuj format logów
4. Sprawdź zmienne środowiskowe

### Za dużo fałszywych alarmów

1. Dostosuj wzorce błędów
2. Zwiększ severity threshold
3. Użyj rate limiting
4. Filtruj po komponentach

### Problemy z wydajnością

1. Zwiększ scan_interval
2. Ogranicz liczbę monitorowanych plików
3. Użyj log rotation
4. Rozważ skalowanie poziome