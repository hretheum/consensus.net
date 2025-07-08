# ConsensusNet - Dokumentacja Użytkownika

> Rewolucyjny system multi-agent AI do zdecentralizowanej weryfikacji faktów z użyciem kolektywnej inteligencji

## 📋 Spis treści

1. [Wprowadzenie](#wprowadzenie)
2. [Instalacja i konfiguracja](#instalacja-i-konfiguracja)
3. [Podstawy korzystania](#podstawy-korzystania)
4. [Endpointy API](#endpointy-api)
5. [Rodzaje weryfikacji](#rodzaje-weryfikacji)
6. [Przykłady użycia](#przykłady-użycia)
7. [Monitorowanie systemu](#monitorowanie-systemu)
8. [Zaawansowane funkcje](#zaawansowane-funkcje)
9. [Rozwiązywanie problemów](#rozwiązywanie-problemów)
10. [FAQ](#faq)

---

## 🎯 Wprowadzenie

ConsensusNet to innowacyjny system multi-agent AI, który wykorzystuje kolektywną inteligencję do walki z dezinformacją. System implementuje architekturę **ECAMAN** (Emergent Consensus through Adversarial Meta-Agent Networks), która orkiestruje wyspecjalizowane agenty AI w debatach adversarialnych i mechanizmach konsensusu.

### Kluczowe cechy

- **🤖 Dynamiczne tworzenie agentów**: Meta-agenty tworzą wyspecjalizowanych weryfikatorów na żądanie
- **⚔️ Weryfikacja adversarialna**: Agenty prokuratorzy/obrońcy aktywnie podważają twierdzenia
- **🛡️ Tolerancja błędów bizantyjskich**: Niezawodny konsensus nawet z zawodnymi agentami
- **🕸️ Sieci zaufania**: System reputacji oparty na grafach dla wiarygodności agentów
- **⚡ Przetwarzanie w czasie rzeczywistym**: Obsługa WebSocket dla aktualizacji weryfikacji na żywo

### Architektura systemu

```
Meta-Agent Orchestrator (Orkiestrator)
    ↓ tworzy
Wyspecjalizowane Agenty → Debaty Adversarialne → Konsensus Ważony Zaufaniem
```

---

## 🚀 Instalacja i konfiguracja

### Wymagania systemowe

- **Python**: 3.11 lub nowszy
- **Docker**: 20.10 lub nowszy
- **Docker Compose**: 2.0 lub nowszy
- **Pamięć RAM**: minimum 4GB, zalecane 8GB
- **Miejsce na dysku**: minimum 2GB

### Instalacja za pomocą Docker (zalecana)

1. **Klonowanie repozytorium**
```bash
git clone https://github.com/hretheum/consensus.net
cd consensus.net
```

2. **Konfiguracja środowiska**
```bash
# Skopiuj przykładowy plik konfiguracji
cp .env.example .env

# Edytuj plik .env i dodaj swoje klucze API
nano .env
```

3. **Uruchomienie wszystkich usług**
```bash
# Uruchom wszystkie kontenery
docker-compose up -d

# Sprawdź status usług
docker-compose ps

# Zobacz logi aplikacji
docker-compose logs -f
```

### Konfiguracja kluczy API

W pliku `.env` skonfiguruj następujące klucze API:

```env
# OpenAI (główny dostawca LLM)
OPENAI_API_KEY=sk-...

# Anthropic (backup)
ANTHROPIC_API_KEY=sk-ant-...

# Konfiguracja bazy danych
POSTGRES_DB=consensus
POSTGRES_USER=consensus
POSTGRES_PASSWORD=devpassword

# Redis
REDIS_URL=redis://localhost:6380

# Środowisko
ENVIRONMENT=development
```

### Dostęp do usług

Po uruchomieniu Docker Compose, następujące usługi będą dostępne:

- **API ConsensusNet**: http://localhost:8000
- **Dokumentacja API**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

---

## 🔧 Podstawy korzystania

### Sprawdzenie stanu systemu

Przed rozpoczęciem weryfikacji sprawdź czy system działa poprawnie:

```bash
# Test podstawowej dostępności
curl http://localhost:8000/

# Szczegółowe sprawdzenie stanu
curl http://localhost:8000/api/health
```

### Pierwsza weryfikacja

Przykład podstawowej weryfikacji twierdzenia:

```bash
curl -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Ziemia jest płaska",
    "metadata": {
      "language": "pl"
    }
  }'
```

### Struktura odpowiedzi

Każda weryfikacja zwraca ustrukturyzowaną odpowiedź:

```json
{
  "success": true,
  "result": {
    "claim": "Ziemia jest płaska",
    "verdict": "FALSE",
    "confidence": 0.99,
    "reasoning": "Istnieją liczne dowody naukowe potwierdzające...",
    "sources": [
      "https://nasa.gov/earth-round-evidence",
      "https://wikipedia.org/wiki/Spherical_Earth"
    ],
    "evidence": [
      {
        "type": "scientific",
        "content": "Zdjęcia satelitarne pokazują...",
        "credibility": 0.95
      }
    ],
    "agent_id": "simple_agent_v1",
    "metadata": {
      "processing_method": "llm_enhanced",
      "llm_provider": "openai"
    }
  },
  "processing_time": 2.34,
  "timestamp": "2025-01-07T10:30:00Z"
}
```

---

## 🌐 Endpointy API

### Podstawowe endpointy

#### `GET /`
**Opis**: Podstawowy endpoint sprawdzania stanu  
**Parametry**: Brak  
**Odpowiedź**: Status aplikacji

#### `GET /api/health`
**Opis**: Szczegółowy stan systemu  
**Parametry**: Brak  
**Odpowiedź**: Status wszystkich komponentów

```json
{
  "status": "healthy",
  "checks": {
    "api": "operational",
    "database": "operational",
    "redis": "operational",
    "agents": "operational",
    "llm_services": "operational"
  }
}
```

### Endpointy weryfikacji

#### `POST /api/verify`
**Opis**: Podstawowa weryfikacja twierdzenia  
**Rate limit**: 10 zapytań/minutę na IP  
**Content-Type**: `application/json`

**Parametry zapytania**:
```json
{
  "claim": "string (1-2000 znaków)",
  "agent_id": "string (opcjonalne)",
  "metadata": {
    "language": "pl|en",
    "priority": "low|normal|high"
  }
}
```

#### `POST /api/verify/enhanced`
**Opis**: Ulepszona weryfikacja z pełną integracją LLM  
**Rate limit**: 10 zapytań/minutę na IP  

**Parametry**: Identyczne jak `/api/verify`  
**Różnica**: Wykorzystuje zaawansowane modele LLM z mechanizmami fallback

#### `POST /api/verify/multi-agent`
**Opis**: Weryfikacja z użyciem systemu multi-agent  
**Rate limit**: 5 zapytań/minutę na IP  

**Funkcje**:
- Równoległe przetwarzanie przez wiele agentów
- Agregacja wyników przez konsensus
- Specjalizacja domenowa agentów

#### `POST /api/verify/adversarial`
**Opis**: Weryfikacja przez debatę adversarialną  
**Rate limit**: 3 zapytania/minutę na IP  

**Proces**:
1. Agent prokurator szuka słabych punktów
2. Agent obrońca przedstawia dowody
3. Moderator syntetyzuje konsensus
4. Dodatkowi eksperci przy niepewności

### Endpointy monitorowania

#### `GET /api/verify/stats`
**Opis**: Statystyki usługi weryfikacji

```json
{
  "status": "operational",
  "service": "verification",
  "total_verifications": 1234,
  "accuracy_rate": 0.89,
  "average_processing_time": 3.2,
  "active_agents": 5
}
```

#### `GET /api/llm/status`
**Opis**: Status dostawców LLM

```json
{
  "status": "operational",
  "llm_services": {
    "openai": {
      "status": "operational",
      "model": "gpt-4o-mini",
      "latency": 1.2
    },
    "anthropic": {
      "status": "operational",
      "model": "claude-3-haiku",
      "latency": 0.8
    },
    "ollama": {
      "status": "operational",
      "model": "llama3.2",
      "latency": 3.5
    }
  }
}
```

#### `GET /api/system/info`
**Opis**: Kompleksowe informacje o systemie

---

## 🔍 Rodzaje weryfikacji

### 1. Weryfikacja podstawowa (`/api/verify`)

**Zastosowanie**: Szybka weryfikacja prostych faktów  
**Czas odpowiedzi**: 1-3 sekundy  
**Dokładność**: ~85% dla prostych faktów  

**Przykład użycia**:
```bash
curl -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Stolica Polski to Warszawa"
  }'
```

### 2. Weryfikacja ulepszona (`/api/verify/enhanced`)

**Zastosowanie**: Złożone twierdzenia wymagające analizy kontekstu  
**Czas odpowiedzi**: 3-8 sekund  
**Dokładność**: ~90% dla złożonych twierdzeń  

**Funkcje**:
- Integracja z najnowszymi modelami LLM
- Automatyczny fallback między dostawcami
- Lepsza kalibracja pewności

**Przykład użycia**:
```bash
curl -X POST "http://localhost:8000/api/verify/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Badania z 2024 roku wykazały że sztuczna inteligencja może zastąpić 40% miejsc pracy do 2030 roku",
    "metadata": {
      "language": "pl",
      "domain": "technology"
    }
  }'
```

### 3. System multi-agent (`/api/verify/multi-agent`)

**Zastosowanie**: Weryfikacja wymagająca ekspertyzy domenowej  
**Czas odpowiedzi**: 5-15 sekund  
**Dokładność**: ~92% dzięki konsensusowi  

**Proces**:
1. **Agent generalista**: Podstawowa weryfikacja
2. **Agent ulepszony**: Analiza z LLM
3. **Agent specjalista**: Analiza domenowa (nauka/wiadomości/technologia)
4. **Konsensus**: Agregacja wyników przez głosowanie większością

**Przykład odpowiedzi**:
```json
{
  "result": {
    "verdict": "TRUE",
    "confidence": 0.87,
    "metadata": {
      "multi_agent_system": "simulation",
      "agent_count": 3,
      "individual_verdicts": ["TRUE", "TRUE", "UNCERTAIN"],
      "consensus_agreement": 0.67,
      "agents_used": ["agent_generalist_1", "agent_enhanced_2", "agent_specialist_3"],
      "domain_specialists": ["generalist", "generalist", "science"]
    }
  }
}
```

### 4. Debata adversarialna (`/api/verify/adversarial`)

**Zastosowanie**: Kontrowersyjne twierdzenia wymagające szczegółowej analizy  
**Czas odpowiedzi**: 10-30 sekund  
**Dokładność**: ~95% dla złożonych przypadków  

**Architektura debaty**:
```
Prokurator → Obrońca → Moderator → [Eksperci] → Konsensus
```

**Przykład użycia**:
```bash
curl -X POST "http://localhost:8000/api/verify/adversarial" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Szczepionki przeciw COVID-19 powodują poważne skutki uboczne u większości pacjentów",
    "metadata": {
      "controversy_level": "high",
      "domain": "medical"
    }
  }'
```

---

## 💡 Przykłady użycia

### Przykład 1: Weryfikacja faktów naukowych

```python
import requests
import json

def verify_scientific_claim(claim):
    url = "http://localhost:8000/api/verify/enhanced"
    
    payload = {
        "claim": claim,
        "metadata": {
            "domain": "science",
            "language": "pl"
        }
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result["success"]:
        verification = result["result"]
        print(f"Twierdzenie: {verification['claim']}")
        print(f"Werdykt: {verification['verdict']}")
        print(f"Pewność: {verification['confidence']:.2%}")
        print(f"Uzasadnienie: {verification['reasoning'][:200]}...")
        print(f"Źródła: {len(verification['sources'])} znalezionych")
    
    return result

# Przykład użycia
result = verify_scientific_claim(
    "Antybiotyki są skuteczne w leczeniu infekcji wirusowych"
)
```

### Przykład 2: Batch weryfikacja wielu twierdzeń

```python
import asyncio
import aiohttp

async def batch_verify(claims, verification_type="basic"):
    endpoint_map = {
        "basic": "/api/verify",
        "enhanced": "/api/verify/enhanced", 
        "multi_agent": "/api/verify/multi-agent",
        "adversarial": "/api/verify/adversarial"
    }
    
    url = f"http://localhost:8000{endpoint_map[verification_type]}"
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for claim in claims:
            task = verify_single_claim(session, url, claim)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

async def verify_single_claim(session, url, claim):
    payload = {"claim": claim}
    async with session.post(url, json=payload) as response:
        return await response.json()

# Przykład użycia
claims = [
    "Ziemia krąży wokół Słońca",
    "Woda wrze w temperaturze 100°C",
    "Człowiek wykorzystuje tylko 10% mózgu"
]

results = asyncio.run(batch_verify(claims, "enhanced"))
for i, result in enumerate(results):
    print(f"Twierdzenie {i+1}: {result['result']['verdict']}")
```

### Przykład 3: Monitoring w czasie rzeczywistym

```python
import requests
import time

def monitor_system_health():
    endpoints = [
        "/api/health",
        "/api/verify/stats", 
        "/api/llm/status",
        "/api/system/info"
    ]
    
    base_url = "http://localhost:8000"
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            data = response.json()
            
            print(f"\n=== {endpoint} ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"Błąd dla {endpoint}: {e}")
        
        time.sleep(1)

# Uruchom monitoring
monitor_system_health()
```

### Przykład 4: Integracja z aplikacją webową

```javascript
// Frontend JavaScript
class ConsensusNetClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async verifyFact(claim, options = {}) {
        const {
            type = 'basic',
            language = 'pl',
            priority = 'normal'
        } = options;
        
        const endpoints = {
            basic: '/api/verify',
            enhanced: '/api/verify/enhanced',
            multiAgent: '/api/verify/multi-agent',
            adversarial: '/api/verify/adversarial'
        };
        
        try {
            const response = await fetch(`${this.baseUrl}${endpoints[type]}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    claim,
                    metadata: { language, priority }
                })
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Verification failed');
            }
            
            return result;
            
        } catch (error) {
            console.error('Verification error:', error);
            throw error;
        }
    }
    
    async getSystemStatus() {
        const response = await fetch(`${this.baseUrl}/api/system/info`);
        return response.json();
    }
}

// Przykład użycia
const client = new ConsensusNetClient();

document.getElementById('verify-btn').addEventListener('click', async () => {
    const claim = document.getElementById('claim-input').value;
    const resultDiv = document.getElementById('result');
    
    if (!claim.trim()) {
        alert('Wprowadź twierdzenie do weryfikacji');
        return;
    }
    
    try {
        resultDiv.innerHTML = '<div class="loading">Weryfikacja w toku...</div>';
        
        const result = await client.verifyFact(claim, { type: 'enhanced' });
        const verification = result.result;
        
        const verdictClass = verification.verdict.toLowerCase();
        const confidencePercent = (verification.confidence * 100).toFixed(1);
        
        resultDiv.innerHTML = `
            <div class="verification-result ${verdictClass}">
                <h3>Wynik weryfikacji</h3>
                <div class="verdict">
                    Werdykt: <span class="verdict-${verdictClass}">${verification.verdict}</span>
                </div>
                <div class="confidence">
                    Pewność: ${confidencePercent}%
                </div>
                <div class="reasoning">
                    <h4>Uzasadnienie:</h4>
                    <p>${verification.reasoning}</p>
                </div>
                <div class="sources">
                    <h4>Źródła (${verification.sources.length}):</h4>
                    <ul>
                        ${verification.sources.map(source => 
                            `<li><a href="${source}" target="_blank">${source}</a></li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="metadata">
                    Czas przetwarzania: ${result.processing_time.toFixed(2)}s
                </div>
            </div>
        `;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error">
                <h3>Błąd weryfikacji</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
});
```

---

## 📊 Monitorowanie systemu

### Sprawdzanie stanu zdrowia systemu

```bash
# Podstawowy status
curl http://localhost:8000/api/health

# Szczegółowe informacje systemowe
curl http://localhost:8000/api/system/info

# Status dostawców LLM
curl http://localhost:8000/api/llm/status

# Statystyki weryfikacji
curl http://localhost:8000/api/verify/stats
```

### Metryki systemowe

ConsensusNet udostępnia następujące metryki:

#### Metryki weryfikacji
- **Łączna liczba weryfikacji**: Wszystkie przeprowadzone weryfikacje
- **Wskaźnik dokładności**: Procent poprawnych weryfikacji
- **Średni czas przetwarzania**: Czas odpowiedzi systemu
- **Aktywne agenty**: Liczba działających agentów

#### Metryki LLM
- **Status dostawców**: OpenAI, Anthropic, Ollama
- **Opóźnienia**: Czasy odpowiedzi poszczególnych modeli
- **Wykorzystanie API**: Liczba wywołań i koszty

#### Metryki systemu
- **Użycie pamięci**: RAM i storage
- **Połączenia bazowe**: PostgreSQL i Redis
- **Rate limiting**: Aktywne ograniczenia

### Logi systemowe

```bash
# Wszystkie logi
docker-compose logs -f

# Tylko API
docker-compose logs -f api

# Tylko baza danych
docker-compose logs -f postgres

# Ostatnie 100 linii
docker-compose logs --tail=100
```

### Automatyczne monitorowanie

Przykładowy skrypt monitorowania:

```bash
#!/bin/bash
# monitor.sh - Skrypt monitorowania ConsensusNet

ENDPOINT="http://localhost:8000"
LOG_FILE="/var/log/consensusnet-monitor.log"

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT/api/health)
    
    if [ "$response" = "200" ]; then
        echo "[$timestamp] HEALTH: OK" >> $LOG_FILE
        return 0
    else
        echo "[$timestamp] HEALTH: FAILED (HTTP $response)" >> $LOG_FILE
        return 1
    fi
}

check_verification() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local test_claim="Test claim for monitoring"
    
    local response=$(curl -s -X POST "$ENDPOINT/api/verify" \
        -H "Content-Type: application/json" \
        -d "{\"claim\":\"$test_claim\"}" \
        -w "%{http_code}")
    
    if echo "$response" | grep -q '"success":true'; then
        echo "[$timestamp] VERIFICATION: OK" >> $LOG_FILE
        return 0
    else
        echo "[$timestamp] VERIFICATION: FAILED" >> $LOG_FILE
        return 1
    fi
}

# Uruchom sprawdzenie co 5 minut
while true; do
    check_health
    sleep 60
    check_verification
    sleep 240
done
```

---

## 🔧 Zaawansowane funkcje

### Konfiguracja agentów

#### Typy agentów dostępnych w systemie:

1. **Simple Agent**: Podstawowy agent weryfikacyjny
2. **Enhanced Agent**: Agent z integracją LLM
3. **Science Agent**: Specjalista od faktów naukowych
4. **News Agent**: Specjalista od aktualności
5. **Tech Agent**: Specjalista od technologii

#### Zarządzanie pulą agentów

```bash
# Sprawdzenie stanu puli agentów
curl http://localhost:8000/api/agents/pool/status

# Inicjalizacja puli agentów
curl -X POST http://localhost:8000/api/agents/pool/initialize

# Dodanie wyspecjalizowanych agentów
curl -X POST http://localhost:8000/api/agents/specialized/add
```

### System reputacji i zaufania

```bash
# Statystyki reputacji
curl http://localhost:8000/api/reputation/stats

# Ranking agentów
curl http://localhost:8000/api/reputation/rankings

# Eksperci domenowi
curl http://localhost:8000/api/reputation/domain-experts/science
```

### Mechanizm debat adversarialnych

System implementuje zaawansowany protokół debat:

1. **Faza przygotowawcza**: Analiza twierdzenia i przydzielenie ról
2. **Runda prokuratorska**: Agent prokurator szuka słabych punktów
3. **Runda obrony**: Agent obrońca przedstawia dowody
4. **Synteza**: Moderator łączy argumenty
5. **Konsultacje eksperckie**: Dodatkowi eksperci przy niepewności >30%

```bash
# Statystyki debat
curl http://localhost:8000/api/debates/stats

# Ostatnie debaty
curl http://localhost:8000/api/debates/recent?limit=10
```

### Swarm Burst Mode

Dla pilnych weryfikacji system może aktywować tryb "burst":

- Tworzy 10-20 micro-agentów na 30 sekund
- Równoległe przetwarzanie różnych aspektów twierdzenia
- Szybki konsensus w czasie <30 sekund

```json
{
  "claim": "BREAKING: Ważne wydarzenie wymaga weryfikacji",
  "metadata": {
    "priority": "urgent",
    "enable_burst": true,
    "time_limit": 30
  }
}
```

### Konfiguracja zaawansowana

#### Zmienne środowiskowe

```env
# Konfiguracja agentów
MAX_AGENTS_PER_VERIFICATION=5
AGENT_TIMEOUT_SECONDS=30
CONSENSUS_THRESHOLD=0.7

# Konfiguracja LLM
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-haiku-20240307
OLLAMA_MODEL=llama3.2

# Konfiguracja debat
ADVERSARIAL_ROUNDS=4
DEBATE_TIMEOUT_SECONDS=120
EXPERT_CONSULTATION_THRESHOLD=0.3

# Konfiguracja systemu zaufania
TRUST_DECAY_RATE=0.01
REPUTATION_UPDATE_FREQUENCY=3600
MIN_TRUST_SCORE=0.1
```

#### Dostosowanie parametrów weryfikacji

```python
# Przykład dostosowania przez metadata
request_payload = {
    "claim": "Twoje twierdzenie",
    "metadata": {
        "verification_parameters": {
            "confidence_threshold": 0.8,
            "max_sources": 10,
            "require_scientific_sources": True,
            "language_preference": "pl",
            "fact_check_depth": "deep"
        },
        "agent_preferences": {
            "prefer_specialist_agents": True,
            "exclude_agents": ["unreliable_agent_id"],
            "force_adversarial": False
        }
    }
}
```

---

## 🚨 Rozwiązywanie problemów

### Typowe problemy i rozwiązania

#### Problem: Błąd połączenia z API
```
curl: (7) Failed to connect to localhost:8000: Connection refused
```

**Rozwiązanie**:
```bash
# Sprawdź czy kontenery działają
docker-compose ps

# Jeśli nie - uruchom ponownie
docker-compose up -d

# Sprawdź logi
docker-compose logs api
```

#### Problem: Błędy autoryzacji LLM
```json
{
  "error": "OpenAI API authentication failed",
  "error_code": "LLM_AUTH_ERROR"
}
```

**Rozwiązanie**:
1. Sprawdź klucze API w pliku `.env`
2. Zweryfikuj ważność kluczy na stronach dostawców
3. Uruchom ponownie kontener po zmianie `.env`:
```bash
docker-compose down
docker-compose up -d
```

#### Problem: Powolne odpowiedzi
```json
{
  "processing_time": 45.2,
  "error": "Request timeout"
}
```

**Rozwiązania**:
1. Sprawdź status LLM: `curl http://localhost:8000/api/llm/status`
2. Użyj prostszego endpointu `/api/verify` zamiast `/api/verify/adversarial`
3. Zwiększ timeout w konfiguracji
4. Sprawdź zasoby systemowe: `docker stats`

#### Problem: Rate limiting
```json
{
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_ERROR"
}
```

**Rozwiązanie**:
- Poczekaj 1 minutę przed kolejnym zapytaniem
- Rate limity: 10/min (basic), 5/min (multi-agent), 3/min (adversarial)

### Diagnostyka systemu

#### Sprawdzenie zasobów
```bash
# Wykorzystanie zasobów przez kontenery
docker stats

# Status wszystkich usług
docker-compose ps

# Sprawdzenie miejsce na dysku
df -h

# Sprawdzenie pamięci
free -h
```

#### Sprawdzenie logów błędów
```bash
# Błędy API
docker-compose logs api | grep ERROR

# Błędy bazy danych
docker-compose logs postgres | grep ERROR

# Wszystkie błędy z ostatnich 24h
docker-compose logs --since="24h" | grep ERROR
```

#### Test końca do końca
```bash
#!/bin/bash
# test_e2e.sh - Test funkcjonalności end-to-end

echo "=== Test podstawowej weryfikacji ==="
response=$(curl -s -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{"claim":"2+2=4"}')

if echo "$response" | grep -q '"success":true'; then
    echo "✓ Podstawowa weryfikacja działa"
else
    echo "✗ Podstawowa weryfikacja nie działa"
    echo "$response"
fi

echo "=== Test weryfikacji ulepszonej ==="
response=$(curl -s -X POST "http://localhost:8000/api/verify/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"claim":"Woda wrze w 100°C"}')

if echo "$response" | grep -q '"success":true'; then
    echo "✓ Weryfikacja ulepszona działa"
else
    echo "✗ Weryfikacja ulepszona nie działa"
fi

echo "=== Test stanu systemu ==="
response=$(curl -s "http://localhost:8000/api/health")

if echo "$response" | grep -q '"status":"healthy"'; then
    echo "✓ System jest zdrowy"
else
    echo "✗ Problemy ze stanem systemu"
    echo "$response"
fi
```

### Kontakt z supportem

W przypadku problemów, których nie można rozwiązać:

1. **Sprawdź dokumentację**: https://github.com/hretheum/consensus.net
2. **Utwórz issue**: https://github.com/hretheum/consensus.net/issues
3. **Załącz logi**: Użyj `docker-compose logs > debug.log`
4. **Opisz środowisko**: OS, Docker version, konfiguracja

---

## ❓ FAQ

### Ogólne pytania

**Q: Czy ConsensusNet może weryfikować fakty w języku polskim?**  
A: Tak, system obsługuje język polski. Dodaj `"language": "pl"` w metadata zapytania.

**Q: Ile kosztuje używanie ConsensusNet?**  
A: System jest open source. Jedyne koszty to wywołania API do dostawców LLM (OpenAI, Anthropic).

**Q: Czy mogę używać ConsensusNet bez kluczy API?**  
A: Tak, system ma tryb symulacji, ale ograniczoną dokładność. Zalecane są klucze API.

### Techniczne pytania

**Q: Jakie są limity zapytań?**  
A: 
- `/api/verify`: 10 zapytań/minutę
- `/api/verify/enhanced`: 10 zapytań/minutę  
- `/api/verify/multi-agent`: 5 zapytań/minutę
- `/api/verify/adversarial`: 3 zapytania/minutę

**Q: Czy mogę zwiększyć limity?**  
A: Tak, zmodyfikuj konfigurację w `src/api/rate_limiter.py` i uruchom ponownie.

**Q: Jak długo przechowywane są wyniki weryfikacji?**  
A: Domyślnie wyniki nie są trwale przechowywane. Możesz skonfigurować persistencję w bazie danych.

**Q: Czy system obsługuje API klucze enterprise?**  
A: Tak, system automatycznie wykryje i wykorzysta klucze enterprise z wyższymi limitami.

### Pytania o dokładność

**Q: Jaka jest dokładność systemu?**  
A:
- Proste fakty: ~85-90%
- Złożone twierdzenia: ~70-80%
- System adversarialny: ~90-95%

**Q: Czy system może się mylić?**  
A: Tak, żaden system AI nie jest idealny. Zawsze sprawdzaj krytyczne informacje w dodatkowych źródłach.

**Q: Jak system radzi sobie z kontrowersjami?**  
A: Controversyjne tematy są kierowane do systemu adversarialnego z wieloma ekspertami.

### Pytania o integrację

**Q: Czy mogę zintegrować ConsensusNet z moją aplikacją?**  
A: Tak, system udostępnia REST API. Zobacz przykłady integracji w dokumentacji.

**Q: Czy jest dostępny SDK?**  
A: Obecnie dostępny jest tylko REST API. SDK w Pythonie i JavaScript są planowane.

**Q: Czy system obsługuje webhooks?**  
A: Obecnie nie, ale funkcja jest planowana w przyszłych wersjach.

### Pytania o deployment

**Q: Czy mogę uruchomić ConsensusNet w chmurze?**  
A: Tak, system jest konteneryzowany i może działać na AWS, GCP, Azure, Digital Ocean.

**Q: Jakie są wymagania sprzętowe dla produkcji?**  
A: Minimum 8GB RAM, 4 CPU cores, 50GB storage. Zalecane 16GB RAM.

**Q: Czy system jest bezpieczny?**  
A: System implementuje rate limiting, walidację input, i może być uruchamiany za reverse proxy.

---

## 📚 Dodatkowe zasoby

### Dokumentacja techniczna
- [Architektura ECAMAN](docs/architecture/ARCHITECTURE_RECOMMENDATION.md)
- [Roadmapa projektu](consensus-roadmap.md)
- [Status rozwoju](STATUS.md)
- [Przewodnik deploymentu](DEPLOYMENT_GUIDE.md)

### API Reference
- [Dokumentacja OpenAPI](http://localhost:8000/api/docs)
- [ReDoc](http://localhost:8000/api/redoc)

### Przykłady i tutoriale
- [Przykłady integracji](docs/examples/)
- [Tutoriale](docs/tutorials/)
- [Najlepsze praktyki](docs/best-practices/)

### Community
- [GitHub Repository](https://github.com/hretheum/consensus.net)
- [GitHub Issues](https://github.com/hretheum/consensus.net/issues)
- [GitHub Discussions](https://github.com/hretheum/consensus.net/discussions)

---

**Ostatnia aktualizacja**: 07.01.2025  
**Wersja dokumentacji**: 1.0  
**Wersja systemu**: 0.1.0