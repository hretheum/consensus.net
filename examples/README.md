# 📚 Przykłady Integracji BugBot

Ten katalog zawiera przykłady różnych sposobów integracji BugBot z aplikacjami.

## 📁 Struktura plików

### 1. **integration_logging.py** - Integracja przez system logowania
- Najprostsza metoda integracji
- Konfiguracja logowania w Python, Node.js, Java
- Strukturalne logowanie błędów
- Helper klasy dla łatwiejszego logowania

### 2. **integration_api.py** - Integracja przez API BugBot
- Klient API do komunikacji z BugBot
- Middleware dla FastAPI
- Dekoratory dla automatycznego monitorowania
- Integracja z Celery
- Webhook handler
- Health check z integracją

### 3. **integration_docker.py** - Integracja Docker i Kubernetes
- Docker Compose konfiguracja
- Dockerfile dla BugBot
- Kubernetes Deployment, Service, DaemonSet
- Sidecar pattern
- Helm chart
- Integracja z Docker SDK
- GitHub Actions integration

### 4. **integration_frameworks.py** - Integracja z popularnymi frameworkami
- Sentry integration
- Prometheus + AlertManager
- Elastic APM
- Datadog
- Django (settings, middleware)
- Flask (error handlers)
- SQLAlchemy (event listeners)
- pytest (test reporter)
- AWS Lambda

## 🚀 Szybki start

### Najprostsza integracja (przez logi)

1. Dodaj logowanie do swojej aplikacji:
```python
import logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

2. Uruchom BugBot:
```bash
export BUGBOT_LOG_DIRS=./logs
python src/services/bugbot/run_bugbot.py
```

### Integracja przez API

1. Zainstaluj klienta:
```python
from examples.integration_api import BugBotAPIClient
client = BugBotAPIClient()
```

2. Raportuj błędy:
```python
await client.report_error({
    "error": "Database connection failed",
    "severity": "high",
    "component": "database"
})
```

### Integracja Docker

1. Użyj docker-compose:
```bash
docker-compose -f examples/docker-compose.yml up
```

## 📋 Wybór metody integracji

| Twoja sytuacja | Zalecana metoda | Przykładowy plik |
|----------------|-----------------|------------------|
| Mała aplikacja, szybka integracja | Pliki logów | `integration_logging.py` |
| Mikroserwisy, natychmiastowe alerty | API + Middleware | `integration_api.py` |
| Kubernetes cluster | DaemonSet lub Sidecar | `integration_docker.py` |
| Django/Flask aplikacja | Framework middleware | `integration_frameworks.py` |
| Istniejący monitoring (Sentry, Datadog) | Hook integration | `integration_frameworks.py` |

## 🔧 Konfiguracja

Wszystkie przykłady używają zmiennych środowiskowych:

```bash
# Podstawowa konfiguracja
export BUGBOT_LOG_DIRS=/path/to/logs
export BUGBOT_SCAN_INTERVAL=10

# Powiadomienia
export BUGBOT_SLACK_WEBHOOK=https://hooks.slack.com/...
export BUGBOT_EMAIL_SMTP_SERVER=smtp.gmail.com

# GitHub integracja
export BUGBOT_GITHUB_TOKEN=ghp_...
export BUGBOT_GITHUB_OWNER=your-org
export BUGBOT_GITHUB_REPO=your-repo
```

## 📖 Dokumentacja

Pełna dokumentacja dostępna w:
- [Główna dokumentacja BugBot](../docs/BUGBOT.md)
- [Przewodnik integracji](../docs/BUGBOT_INTEGRATION_GUIDE.md)

## ❓ Pomoc

Jeśli masz pytania lub problemy:
1. Sprawdź [Troubleshooting](../docs/BUGBOT_INTEGRATION_GUIDE.md#troubleshooting)
2. Zobacz [FAQ](../docs/BUGBOT.md#rozwiązywanie-problemów)
3. Utwórz issue w repozytorium