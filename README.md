# ConsensusNet

> Revolutionary multi-agent AI system for decentralized fact-checking using collective intelligence

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/hretheum/consensus.net?style=social)](https://github.com/hretheum/consensus.net/stargazers)
[![Development Status](https://img.shields.io/badge/status-pre--alpha-red.svg)](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md)

## 🎯 Overview

ConsensusNet is an innovative multi-agent AI system that leverages collective intelligence to combat misinformation. By orchestrating specialized AI agents in adversarial debates and consensus mechanisms, it achieves unprecedented accuracy in fact-checking.

## ✨ Key Features

- **Dynamic Agent Spawning**: Meta-agents create specialized verifiers on-demand
- **Adversarial Verification**: Prosecutor/Defender agents actively challenge claims  
- **Byzantine Fault Tolerance**: Robust consensus even with unreliable agents
- **Trust Networks**: Graph-based reputation system for agent credibility
- **Real-time Processing**: WebSocket support for live verification updates
- **BugBot Integration**: Automatic error detection and management system

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/hretheum/consensus.net
cd consensus.net

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys

# Start all services with Docker
docker-compose up -d

# Check service status
docker-compose ps

# Access the API
curl http://localhost:8000/api/health
```

**Local Services:**
- API: http://localhost:8000
- PostgreSQL: localhost:5433 (user: consensus, pass: devpassword)
- Redis: localhost:6380

### 🌐 Live Demo (Coming Week 3!)
- API: https://api.consensus.net/verify
- Docs: https://api.consensus.net/docs

## 📚 Documentation

- [Architecture Overview](docs/architecture/ARCHITECTURE_RECOMMENDATION.md)
- [Development Setup](docs/development/setup-guide.md)
- [API Reference](docs/api/api-design.md)
- [Research Background](docs/research/agent-architectures-research.md)
- [BugBot Documentation](docs/BUGBOT.md) - Automatic error detection system
- [BugBot Integration Guide](docs/BUGBOT_INTEGRATION_GUIDE.md)

## 🏗️ Architecture

ConsensusNet implements ECAMAN (Emergent Consensus through Adversarial Meta-Agent Networks):

```
Meta-Agent Orchestrator
    ↓ spawns
Specialized Agents → Adversarial Debates → Trust-Weighted Consensus
```

## �️ Developer Tools

### 🐛 BugBot - Automatic Error Detection
BugBot is an integrated error monitoring system that automatically:
- Scans application logs for errors and exceptions
- Analyzes root causes and suggests fixes
- Creates GitHub issues for critical errors
- Sends notifications via Slack, Discord, Email, Teams
- Provides API endpoints for error statistics

See [BugBot Documentation](docs/BUGBOT.md) and [Integration Examples](examples/)

## �📈 Project Status

**Current Phase**: Phase 1 - Foundation Development (Week 1/12)  
**Expected MVP**: April 2025  
**Roadmap**: See [consensus-roadmap.md](consensus-roadmap.md) for detailed timeline

### Completed ✅
- [x] Project structure and documentation
- [x] GitHub repository setup
- [x] GitHub Pages configuration
- [x] Initial project planning
- [x] Container-first architecture
- [x] Docker environment setup and testing
- [x] Basic FastAPI application with health checks
- [x] CI/CD pipeline configuration (GitHub Actions)

### In Progress 🚧
- [x] Development environment setup (Issue #1) ✅
- [ ] Database schema design (Issue #2) ← **Current Focus**
- [ ] Base agent implementation (Issue #3)

### Upcoming 📅
- [ ] Simple fact checker agent (Issue #4)
- [ ] FastAPI gateway (Issue #5)
- [ ] Multi-agent orchestration
- [ ] Consensus mechanisms
- [ ] Frontend development

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📊 Research

This project advances multi-agent AI research with publications targeting:
- ICML/NeurIPS (Consensus mechanisms)
- AAAI/IJCAI (Trust calibration)
- ACL (Misinformation detection)

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with cutting-edge research from OpenAI, Anthropic, and DeepMind.
