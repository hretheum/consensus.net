---
layout: default
title: "ConsensusNet - Dokumentacja Użytkownika"
lang: pl
---

<div style="text-align: right; margin-bottom: 1rem;">
  <a href="/consensus.net/en/" style="text-decoration: none; padding: 0.5rem 1rem; border: 1px solid #0366d6; border-radius: 4px; color: #0366d6; font-size: 0.9em;">
    🇺🇸 English
  </a>
  <a href="/consensus.net/" style="text-decoration: none; padding: 0.5rem 1rem; border: 1px solid #666; border-radius: 4px; color: #666; font-size: 0.9em; margin-left: 0.5rem;">
    🏠 Strona główna
  </a>
</div>

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

### 3. System multi-agent (`/api/verify/multi-agent`)

**Zastosowanie**: Weryfikacja wymagająca ekspertyzy domenowej  
**Czas odpowiedzi**: 5-15 sekund  
**Dokładność**: ~92% dzięki konsensusowi  

**Proces**:
1. **Agent generalista**: Podstawowa weryfikacja
2. **Agent ulepszony**: Analiza z LLM
3. **Agent specjalista**: Analiza domenowa (nauka/wiadomości/technologia)
4. **Konsensus**: Agregacja wyników przez głosowanie większością

### 4. Debata adversarialna (`/api/verify/adversarial`)

**Zastosowanie**: Kontrowersyjne twierdzenia wymagające szczegółowej analizy  
**Czas odpowiedzi**: 10-30 sekund  
**Dokładność**: ~95% dla złożonych przypadków  

**Architektura debaty**:
```
Prokurator → Obrońca → Moderator → [Eksperci] → Konsensus
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

### Przykład 2: Integracja z aplikacją webową

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

---

## 🔧 Zaawansowane funkcje

### Konfiguracja agentów

#### Typy agentów dostępnych w systemie:

1. **Simple Agent**: Podstawowy agent weryfikacyjny
2. **Enhanced Agent**: Agent z integracją LLM
3. **Science Agent**: Specjalista od faktów naukowych
4. **News Agent**: Specjalista od aktualności
5. **Tech Agent**: Specjalista od technologii

### Mechanizm debat adversarialnych

System implementuje zaawansowany protokół debat:

1. **Faza przygotowawcza**: Analiza twierdzenia i przydzielenie ról
2. **Runda prokuratorska**: Agent prokurator szuka słabych punktów
3. **Runda obrony**: Agent obrońca przedstawia dowody
4. **Synteza**: Moderator łączy argumenty
5. **Konsultacje eksperckie**: Dodatkowi eksperci przy niepewności >30%

### Swarm Burst Mode

Dla pilnych weryfikacji system może aktywować tryb "burst":

- Tworzy 10-20 micro-agentów na 30 sekund
- Równoległe przetwarzanie różnych aspektów twierdzenia
- Szybki konsensus w czasie <30 sekund

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

### Pytania o dokładność

**Q: Jaka jest dokładność systemu?**  
A:
- Proste fakty: ~85-90%
- Złożone twierdzenia: ~70-80%
- System adversarialny: ~90-95%

**Q: Czy system może się mylić?**  
A: Tak, żaden system AI nie jest idealny. Zawsze sprawdzaj krytyczne informacje w dodatkowych źródłach.

### Pytania o integrację

**Q: Czy mogę zintegrować ConsensusNet z moją aplikacją?**  
A: Tak, system udostępnia REST API. Zobacz przykłady integracji powyżej.

**Q: Czy jest dostępny SDK?**  
A: Obecnie dostępny jest tylko REST API. SDK w Pythonie i JavaScript są planowane.

### Pytania o deployment

**Q: Czy mogę uruchomić ConsensusNet w chmurze?**  
A: Tak, system jest konteneryzowany i może działać na AWS, GCP, Azure, Digital Ocean.

**Q: Jakie są wymagania sprzętowe dla produkcji?**  
A: Minimum 8GB RAM, 4 CPU cores, 50GB storage. Zalecane 16GB RAM.

---

## 📚 Dodatkowe zasoby

### Dokumentacja techniczna
- [Architektura ECAMAN](https://github.com/hretheum/consensus.net/blob/main/docs/architecture/ARCHITECTURE_RECOMMENDATION.md)
- [Roadmapa projektu](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md)
- [Status rozwoju](https://github.com/hretheum/consensus.net/blob/main/STATUS.md)
- [Przewodnik deploymentu](https://github.com/hretheum/consensus.net/blob/main/DEPLOYMENT_GUIDE.md)

### API Reference
- [Dokumentacja OpenAPI](http://localhost:8000/api/docs)
- [ReDoc](http://localhost:8000/api/redoc)

### Community
- [GitHub Repository](https://github.com/hretheum/consensus.net)
- [GitHub Issues](https://github.com/hretheum/consensus.net/issues)
- [GitHub Discussions](https://github.com/hretheum/consensus.net/discussions)

---

<div style="text-align: center; margin-top: 3rem; padding: 2rem; background: #f6f8fa; border-radius: 6px;">
  <p><strong>Ostatnia aktualizacja</strong>: 07.01.2025</p>
  <p><strong>Wersja dokumentacji</strong>: 1.0</p>
  <p><strong>Wersja systemu</strong>: 0.1.0</p>
</div>