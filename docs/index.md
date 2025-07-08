---
layout: default
title: "ConsensusNet Documentation"
---

<div style="text-align: center; padding: 2rem 0;">
  <h1>🤖 ConsensusNet</h1>
  <p style="font-size: 1.2em; color: #666; margin-bottom: 2rem;">
    Revolutionary multi-agent AI system for decentralized fact-checking<br/>
    using collective intelligence
  </p>
  
  <div style="display: inline-block; border: 1px solid #ddd; border-radius: 8px; padding: 2rem; background: #f9f9f9; margin-bottom: 2rem;">
    <h2 style="margin-top: 0;">📚 Choose Your Language / Wybierz język</h2>
    
    <div style="display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap;">
      <a href="/consensus.net/en/" style="text-decoration: none; display: block; padding: 1rem 2rem; border: 2px solid #0366d6; border-radius: 6px; background: white; color: #0366d6; font-weight: bold; transition: all 0.2s;">
        🇺🇸 English Documentation
      </a>
      
      <a href="/consensus.net/pl/" style="text-decoration: none; display: block; padding: 1rem 2rem; border: 2px solid #d73a49; border-radius: 6px; background: white; color: #d73a49; font-weight: bold; transition: all 0.2s;">
        🇵🇱 Dokumentacja Polski
      </a>
    </div>
  </div>
</div>

## 🎯 Quick Overview

ConsensusNet implements the **ECAMAN** (Emergent Consensus through Adversarial Meta-Agent Networks) architecture:

```
Meta-Agent Orchestrator
    ↓ spawns
Specialized Agents → Adversarial Debates → Trust-Weighted Consensus
```

### Key Features

- **🤖 Dynamic Agent Spawning**: Meta-agents create specialized verifiers on-demand
- **⚔️ Adversarial Verification**: Prosecutor/Defender agents actively challenge claims  
- **🛡️ Byzantine Fault Tolerance**: Robust consensus even with unreliable agents
- **🕸️ Trust Networks**: Graph-based reputation system for agent credibility
- **⚡ Real-time Processing**: WebSocket support for live verification updates

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/hretheum/consensus.net
cd consensus.net

# Start with Docker
docker-compose up -d

# Test the API
curl http://localhost:8000/api/health
```

## 📊 Project Status

**Current Phase**: Phase 1 - Foundation Development  
**Expected MVP**: April 2025  
**License**: MIT

### Completed ✅
- [x] Project structure and documentation
- [x] GitHub repository setup and GitHub Pages
- [x] Container-first architecture  
- [x] Basic FastAPI application with health checks
- [x] Multi-language documentation

### In Progress 🚧
- [ ] Database schema design
- [ ] Base agent implementation
- [ ] Multi-agent orchestration

## 🔗 Resources

- **📖 Documentation**: Choose your language above
- **🔧 API Reference**: [Interactive API Docs](http://localhost:8000/api/docs)
- **💻 GitHub Repository**: [github.com/hretheum/consensus.net](https://github.com/hretheum/consensus.net)
- **📋 Project Board**: [GitHub Issues](https://github.com/hretheum/consensus.net/issues)
- **📈 Roadmap**: [12-week development plan](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/hretheum/consensus.net/blob/main/CONTRIBUTING.md) for details.

---

<div style="text-align: center; margin-top: 3rem; padding: 2rem; background: #f6f8fa; border-radius: 6px;">
  <p><strong>Built with cutting-edge research from OpenAI, Anthropic, and DeepMind</strong></p>
  <p style="margin: 0; color: #666;">Last updated: January 7, 2025 | Version: 0.1.0</p>
</div>

<style>
  a:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
  }
  
  .language-bash {
    background: #f6f8fa;
    border-left: 4px solid #0366d6;
    padding: 1rem;
    margin: 1rem 0;
  }
</style>