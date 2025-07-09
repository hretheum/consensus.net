# Adaptive Source Credibility Evolution - Quick Start Guide

## 🚀 Quick Setup

1. **Configure API Keys** (copy `.env.example` to `.env`):
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY or ANTHROPIC_API_KEY (at least one required)
# - NEWSAPI_KEY (optional, for news sources)
# - GOOGLE_API_KEY and GOOGLE_CSE_ID (optional, for web search)
```

2. **Test the System**:
```bash
python test_adaptive_credibility.py
```

3. **Start the API**:
```bash
docker-compose up
```

## 📊 Key Features

### Automatic Source Selection
The system automatically selects the best sources based on claim domain:
- **Health claims** → PubMed, WHO, CDC
- **Science claims** → arXiv, Nature, Science
- **News claims** → NewsAPI, Reuters, BBC
- **General claims** → Wikipedia, Google Search

### Adaptive LLM Routing
- **High quality evidence (>0.8)** → GPT-4o-mini (cheapest)
- **Medium quality (0.65-0.8)** → GPT-4o-mini or Claude 3 Haiku
- **Low quality (<0.65)** → Claude 3 Haiku (best reasoning)
- **Privacy sensitive** → Llama 3.2 (local)

## 🔍 API Examples

### Basic Verification with Adaptive Sources
```bash
curl -X POST "http://localhost:8000/api/verify/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "COVID-19 vaccines are safe and effective"
  }'
```

### Check Source Statistics
```bash
curl http://localhost:8000/api/sources/stats
```

### Test Individual Source
```bash
curl -X POST "http://localhost:8000/api/sources/test/pubmed?query=vaccine%20safety"
```

## 💰 Cost Optimization

### Free Tier Usage
- **Wikipedia**: Unlimited
- **PubMed**: 3 requests/second
- **arXiv**: Reasonable use
- **NewsAPI**: 100 requests/day
- **Google Search**: 100 requests/day

### Estimated Costs
- **Development**: $0-50/month (mostly free tiers)
- **Production (100 users)**: $200-500/month
- **Scale (1000+ users)**: $1000-2500/month

## 📈 Monitoring Performance

### Python Example
```python
import requests

# Get source credibility scores
stats = requests.get("http://localhost:8000/api/sources/stats").json()

# Monitor which sources are performing well
for source, data in stats["credibility_scores"].items():
    print(f"{source}: {data['current_score']:.3f} ({data['tier']})")
```

### Key Metrics to Watch
- **Evidence Quality Score**: Higher is better (0.0-1.0)
- **Source Credibility**: Evolves based on performance
- **LLM Model Used**: Shows cost optimization
- **Consensus Level**: Agreement among sources

## 🛠️ Troubleshooting

### No API Keys
The system will still work using:
- Wikipedia (always free)
- Simulated evidence (fallback)
- Local Llama 3.2 (if installed)

### Rate Limits
The system automatically:
- Respects API rate limits
- Caches results (1 hour to 7 days)
- Falls back to alternative sources

### Low Evidence Quality
When evidence quality is low:
- Automatically uses better LLM models
- Clearly indicates uncertainty in results
- Suggests consulting additional sources

## 📚 Full Documentation

See [ADAPTIVE_SOURCE_CREDIBILITY_EVOLUTION.md](ADAPTIVE_SOURCE_CREDIBILITY_EVOLUTION.md) for complete system documentation.