# 🚀 Szybki Start - Integracja BugBot

## 1. Uruchom przykładową aplikację

```bash
# Terminal 1
python examples/integration_example_app.py
```

Aplikacja uruchomi się na http://localhost:8001

## 2. Uruchom BugBot

```bash
# Terminal 2
export BUGBOT_LOG_DIRS=./logs
python src/services/bugbot/run_bugbot.py
```

BugBot API będzie dostępne na http://localhost:8000

## 3. Uruchom demo integracji

```bash
# Terminal 3
python examples/demo_integration.py
```

Demo pokaże:
- ✅ Jak aplikacja generuje błędy
- ✅ Jak BugBot je wykrywa
- ✅ Jak błędy są analizowane
- ✅ Jakie akcje są podejmowane

## 4. Sprawdź wyniki

### Dashboard API
http://localhost:8000/api/docs#/bugbot

### Wykryte błędy
```bash
curl http://localhost:8000/api/bugbot/bugs | jq
```

### Statystyki
```bash
curl http://localhost:8000/api/bugbot/stats | jq
```

### Logi aplikacji
```bash
tail -f logs/app_errors.log
```

## 5. Testuj ręcznie

### Generuj błąd NoneType:
```bash
curl http://localhost:8001/api/users/999
```

### Generuj timeout:
```bash
curl http://localhost:8001/api/users/666
```

### Generuj zestaw błędów:
```bash
curl -X POST http://localhost:8001/test/generate-errors
```

## 🎯 Co dalej?

1. **Skonfiguruj powiadomienia** - ustaw zmienne środowiskowe dla Slack/Discord
2. **Połącz z GitHub** - dodaj token dla automatycznych issues
3. **Dostosuj wzorce** - edytuj patterns w config.py
4. **Integruj ze swoją aplikacją** - zobacz przykłady w examples/