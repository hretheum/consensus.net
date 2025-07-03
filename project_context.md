# ConsensusNet Project Context

## 🎯 Quick Project Overview

**ConsensusNet** is an innovative multi-agent AI system for decentralized fact-checking, using collective intelligence to combat misinformation. The project aims to position the creator as an AI researcher on LinkedIn through cutting-edge implementation and research publications.

**Project Status**: Pre-development (as of 03.07.2025)  
**Timeline**: 12 weeks to MVP  
**Budget**: $40-100/month (Digital Ocean)  
**Location**: `/Users/hretheum/dev/bezrobocie/consenus`  
**Repository**: https://github.com/hretheum/consensus.net

## 🏗️ Core Architecture: ECAMAN

**Emergent Consensus through Adversarial Meta-Agent Networks** - A revolutionary 3-layer architecture combining:

1. **Meta-Agent Orchestrator** - Dynamically spawns specialized verification agents
2. **Adversarial Debate Arena** - Prosecutor/Defender/Moderator agents challenge claims
3. **Graph-Based Consensus Network** - Trust-weighted voting with Byzantine fault tolerance

Key innovations: Dynamic agent spawning, adversarial verification, swarm bursts, memory mesh architecture.

## 📚 Essential Documents Map

### Strategic Documents
- **[docs/planning/original-plan.md](./docs/planning/original-plan.md)** - Original project vision and high-level plan
- **[docs/architecture/ARCHITECTURE_RECOMMENDATION.md](./docs/architecture/ARCHITECTURE_RECOMMENDATION.md)** - Detailed ECAMAN architecture specification ⭐
- **[consensus-roadmap.md](./consensus-roadmap.md)** - 12-week atomic task breakdown with success metrics ⭐

### Research & Background
- **[docs/research/agent-architectures-research.md](./docs/research/agent-architectures-research.md)** - Comprehensive research on cutting-edge agent architectures

## 🔑 Key Technical Decisions

### Tech Stack
- **Backend**: Python 3.11+, FastAPI, LangChain
- **LLMs**: GPT-4o-mini (primary), Ollama/Llama 3.2 (fallback)
- **Databases**: PostgreSQL + pgvector, Redis
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Infrastructure**: Docker, Digital Ocean droplet

### Unique Features
1. **Dynamic Agent Spawning** - Meta-agent creates specialists on-demand
2. **Adversarial Debates** - Agents actively challenge each other
3. **Trust Networks** - Graph-based reputation system
4. **Swarm Bursts** - 10-20 micro-agents for urgent verifications

## 📊 Success Metrics

- **Technical**: 90%+ accuracy simple facts, <5s latency
- **Research**: 2+ papers, 1000+ GitHub stars
- **Adoption**: 100+ DAU within 3 months
- **LinkedIn**: Position as AI researcher through publications and demos

## 🚀 Current Phase & Next Steps

**Current**: Phase 0 - Project Setup  
**Next Immediate Tasks**:
1. Setup GitHub repository structure
2. Initialize development environment
3. Create database schemas
4. Implement BaseAgent class

See [consensus-roadmap.md](./consensus-roadmap.md) for detailed task breakdown.

## 💡 Context for AI Assistant

When continuing work on this project, the AI should:

1. **Maintain the vision** of creating a revolutionary fact-checking system that showcases AI research capabilities
2. **Follow ECAMAN architecture** as specified in docs/architecture/ARCHITECTURE_RECOMMENDATION.md
3. **Use the roadmap** for task prioritization and success metrics
4. **Consider budget constraints** - optimize for Digital Ocean deployment
5. **Focus on research impact** - every component should be potentially publishable

### Key Questions to Consider
- How can each feature contribute to a research paper?
- What makes this different from existing fact-checkers?
- How to demonstrate emergent behaviors in multi-agent systems?
- What metrics best showcase the system's innovation?

## 🔗 Quick Command Reference

```bash
# Navigate to project
cd /Users/hretheum/dev/bezrobocie/consenus

# Activate environment (after setup)
source venv/bin/activate

# Run tests
pytest

# Start development server
docker-compose up -d
python src/main.py
```

## 📝 Document Maintenance Notes

- **docs/planning/original-plan.md** - Original vision, keep as historical reference
- **docs/architecture/ARCHITECTURE_RECOMMENDATION.md** - Living document, update with implementation learnings
- **consensus-roadmap.md** - Update weekly with progress
- **This file** - Update when major decisions or changes occur

---

*For deep technical details, start with docs/architecture/ARCHITECTURE_RECOMMENDATION.md. For implementation tasks, see consensus-roadmap.md.*