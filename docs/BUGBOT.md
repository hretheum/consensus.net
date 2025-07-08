# 🐛 BugBot - Automatyczny System Wykrywania i Zarządzania Błędami

## Spis treści

1. [Wprowadzenie](#wprowadzenie)
2. [Architektura](#architektura)
3. [Instalacja i Konfiguracja](#instalacja-i-konfiguracja)
4. [Uruchomienie](#uruchomienie)
5. [API](#api)
6. [Integracje](#integracje)
7. [Przykłady użycia](#przykłady-użycia)

## Wprowadzenie

BugBot to zaawansowany system automatycznego wykrywania, analizy i zarządzania błędami w aplikacjach. System monitoruje logi aplikacji, wykrywa błędy używając wzorców regex, analizuje je pod kątem przyczyn i sugeruje rozwiązania, a następnie automatycznie tworzy raporty i powiadomienia.

### Główne funkcje:

- 🔍 **Automatyczne wykrywanie błędów** - skanowanie logów w czasie rzeczywistym
- 🧠 **Inteligentna analiza** - kategoryzacja, określanie przyczyn i sugerowanie rozwiązań
- 🔔 **Powiadomienia wielokanałowe** - Slack, Discord, Email, Teams, webhooks
- 🐙 **Integracja z GitHub** - automatyczne tworzenie issues
- 📊 **Statystyki i raporty** - dashboardy i podsumowania
- 🚨 **Eskalacja błędów** - automatyczne podnoszenie priorytetu powtarzających się problemów

## Architektura

### Komponenty systemu:

```
┌─────────────────────────────────────────────────────────────────┐
│                         BugBot Core                             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐           │
│  │   Monitor   │─▶│  Analyzer   │─▶│   Notifier   │           │
│  └─────────────┘  └─────────────┘  └──────────────┘           │
│         │                │                   │                   │
│         │                │                   │                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐           │
│  │Log Scanner  │  │Root Cause   │  │Slack/Discord │           │
│  │Pattern Match│  │Analysis     │  │Email/Teams   │           │
│  │Error Queue  │  │Suggestions  │  │Webhooks      │           │
│  └─────────────┘  └─────────────┘  └──────────────┘           │
│                                                                 │
│  ┌─────────────────────────────────────────────────┐           │
│  │              GitHub Integration                  │           │
│  │  - Create Issues                                │           │
│  │  - Update Status                                │           │
│  │  - Manage Labels                                │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Klasy główne:

1. **BugBot** - główny orchestrator
2. **ErrorMonitor** - monitorowanie i wykrywanie błędów
3. **ErrorAnalyzer** - analiza i kategoryzacja
4. **NotificationManager** - zarządzanie powiadomieniami
5. **GitHubIntegration** - integracja z GitHub

## Instalacja i Konfiguracja

### 1. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 2. Konfiguracja przez zmienne środowiskowe

```bash
# Podstawowa konfiguracja
export BUGBOT_PROCESS_INTERVAL=10
export BUGBOT_LOG_DIRS=/app/logs,/var/log/myapp
export BUGBOT_DEFAULT_ASSIGNEE=team-lead

# Eskalacja
export BUGBOT_ESCALATION_THRESHOLD=10
export BUGBOT_ESCALATION_TIME=3600

# Slack
export BUGBOT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK
export BUGBOT_SLACK_CHANNEL=#bugs

# Discord
export BUGBOT_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK

# Email
export BUGBOT_EMAIL_SMTP_SERVER=smtp.gmail.com
export BUGBOT_EMAIL_USERNAME=your-email@gmail.com
export BUGBOT_EMAIL_PASSWORD=your-app-password
export BUGBOT_EMAIL_FROM=bugbot@example.com
export BUGBOT_EMAIL_TO=dev-team@example.com

# GitHub
export BUGBOT_GITHUB_TOKEN=ghp_your_token_here
export BUGBOT_GITHUB_OWNER=your-org
export BUGBOT_GITHUB_REPO=your-repo
```

### 3. Konfiguracja przez plik JSON

Wygeneruj przykładowy plik konfiguracyjny:

```bash
python src/services/bugbot/run_bugbot.py --generate-config
```

To utworzy plik `bugbot-config.example.json`:

```json
{
  "process_interval": 10.0,
  "bugs_storage_path": "./data/bugs.json",
  "escalation_threshold": 10,
  "escalation_time_threshold": 3600,
  "component_owners": {
    "api": "backend-dev",
    "frontend": "frontend-dev",
    "database": "dba"
  },
  "monitor_config": {
    "log_directories": ["./logs"],
    "scan_interval": 10,
    "custom_patterns": [
      {
        "name": "payment_error",
        "pattern": "PAYMENT_FAILED.*",
        "severity": "critical",
        "category": "runtime"
      }
    ]
  },
  "notification_config": {
    "slack": {
      "webhook_url": "https://hooks.slack.com/...",
      "channel": "#bugs",
      "enabled": true
    }
  }
}
```

## Uruchomienie

### 1. Uruchomienie standalone

```bash
# Z domyślną konfiguracją (zmienne środowiskowe)
python src/services/bugbot/run_bugbot.py

# Z plikiem konfiguracyjnym
python src/services/bugbot/run_bugbot.py -c bugbot-config.json
```

### 2. Uruchomienie z API

```bash
# Uruchom główną aplikację z BugBot API
python src/main.py
```

### 3. Docker

```dockerfile
# Dodaj do docker-compose.yml
bugbot:
  build: .
  command: python src/services/bugbot/run_bugbot.py
  volumes:
    - ./logs:/app/logs
    - ./data:/app/data
  environment:
    - BUGBOT_LOG_DIRS=/app/logs
    - BUGBOT_SLACK_WEBHOOK=${BUGBOT_SLACK_WEBHOOK}
```

## API

BugBot udostępnia RESTful API pod `/api/bugbot`:

### Endpoints:

#### GET `/api/bugbot/status`
Pobiera status BugBota

```json
{
  "running": true,
  "bugs_count": 15,
  "last_scan": "2024-01-15T10:30:00",
  "monitored_files": 3
}
```

#### GET `/api/bugbot/bugs`
Lista błędów z filtrowaniem

Parametry:
- `severity` - filtruj po severity (critical, high, medium, low)
- `category` - filtruj po kategorii (runtime, syntax, performance, security)
- `component` - filtruj po komponencie
- `status` - filtruj po statusie (new, assigned, in_progress, resolved)

#### GET `/api/bugbot/bugs/{bug_id}`
Szczegóły konkretnego błędu

#### PATCH `/api/bugbot/bugs/{bug_id}/status`
Aktualizacja statusu błędu

#### GET `/api/bugbot/stats`
Statystyki błędów

#### POST `/api/bugbot/patterns`
Dodanie niestandardowego wzorca błędu

```json
{
  "name": "custom_error",
  "pattern": "CRITICAL:.*payment.*failed",
  "severity": "critical",
  "category": "runtime"
}
```

#### POST `/api/bugbot/scan`
Wymuszenie natychmiastowego skanowania

#### POST `/api/bugbot/test-notification`
Test powiadomień

## Integracje

### Slack

BugBot wysyła sformatowane wiadomości do Slack:

```
🟠 [HIGH] Nowy błąd: Database connection timeout

Severity: HIGH
Kategoria: performance
Komponent: database
Przypisany do: dba

Opis:
Błąd wykryty w pliku: /app/logs/application.log
Linia: 1234

Sugerowana naprawa:
Zwiększ timeout lub zoptymalizuj operację. Sprawdź połączenie sieciowe.

Bug ID: abc123
Częstotliwość: 5
```

### GitHub

BugBot automatycznie tworzy issues w GitHub:

- Dodaje odpowiednie etykiety (severity, component, bugbot)
- Przypisuje do odpowiednich osób
- Formatuje opis z analizą i sugestiami
- Dodaje stack trace jeśli dostępny

### Email

Wysyła sformatowane emaile HTML z:
- Podsumowaniem błędu
- Linkami do szczegółów
- Statystykami

## Przykłady użycia

### 1. Test demonstracyjny

```bash
# Uruchom skrypt testowy
python test_bugbot.py
```

Skrypt:
- Generuje przykładowe błędy w logach
- Testuje API BugBot
- Pokazuje wykryte błędy i statystyki

### 2. Monitorowanie własnej aplikacji

```python
# Dodaj do swojej aplikacji
import logging

# Skonfiguruj logging do pliku
logging.basicConfig(
    filename='logs/myapp.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# BugBot automatycznie wykryje błędy
try:
    risky_operation()
except Exception as e:
    logging.error(f"Operation failed: {e}", exc_info=True)
```

### 3. Niestandardowe wzorce

```python
# Dodaj wzorzec przez API
import requests

pattern = {
    "name": "payment_timeout",
    "pattern": r"Payment gateway timeout.*stripe",
    "severity": "critical",
    "category": "runtime"
}

response = requests.post(
    "http://localhost:8000/api/bugbot/patterns",
    json=pattern
)
```

### 4. Integracja z CI/CD

```yaml
# .github/workflows/bugbot.yml
name: BugBot Monitoring

on:
  workflow_run:
    workflows: ["Tests"]
    types: [completed]

jobs:
  scan-logs:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger BugBot scan
        run: |
          curl -X POST http://your-api/api/bugbot/scan
```

## Wzorce błędów

BugBot domyślnie wykrywa:

1. **Wyjątki Python** - Traceback, Exception, Error
2. **Błędy logów** - ERROR, CRITICAL, WARNING
3. **Błędy pamięci** - MemoryError, OutOfMemoryError
4. **Błędy czasowe** - TimeoutError, Connection timeout
5. **Błędy bazy danych** - DatabaseError, OperationalError
6. **Błędy uprawnień** - PermissionError, Access denied
7. **Błędy HTTP** - 4xx, 5xx
8. **Błędy składni** - SyntaxError, IndentationError

## Dobre praktyki

1. **Strukturyzuj logi** - używaj spójnego formatu logów
2. **Kategoryzuj komponenty** - oznaczaj logi nazwami komponentów
3. **Konfiguruj eskalację** - ustaw progi dla krytycznych błędów
4. **Testuj powiadomienia** - regularnie sprawdzaj kanały
5. **Przeglądaj statystyki** - analizuj trendy błędów
6. **Aktualizuj wzorce** - dodawaj wzorce dla specyficznych błędów

## Rozwiązywanie problemów

### BugBot nie wykrywa błędów
- Sprawdź czy katalogi logów istnieją
- Sprawdź uprawnienia do odczytu plików
- Zweryfikuj wzorce błędów

### Powiadomienia nie działają
- Sprawdź konfigurację webhooków
- Testuj pojedyncze kanały
- Sprawdź logi BugBota

### Za dużo fałszywych alarmów
- Dostosuj wzorce błędów
- Zwiększ próg eskalacji
- Skonfiguruj rate limiting