# ConsensusNet Project Context

## 🎯 Quick Project Overview

**ConsensusNet** is an innovative multi-agent AI system for decentralized fact-checking, using collective intelligence to combat misinformation. The project aims to position the creator as an AI researcher on LinkedIn through cutting-edge implementation and research publications.

**Project Status**: Active Development - Phase 1 Started (as of 03.07.2025 13:50 CET)  
**Timeline**: 12 weeks to MVP (Week 0 completed, Week 1 in progress)  
**Budget**: $40-100/month (Digital Ocean)  
**Location**: `/Users/hretheum/dev/bezrobocie/consenus`  
**Repository**: https://github.com/hretheum/consensus.net  
**GitHub Pages**: https://hretheum.github.io/consensus.net  
**Issues Created**: 5 initial issues for Phase 0-1

## 🏗️ Core Architecture: ECAMAN

**Emergent Consensus through Adversarial Meta-Agent Networks** - A revolutionary 3-layer architecture combining:

1. **Meta-Agent Orchestrator** - Dynamically spawns specialized verification agents
2. **Adversarial Debate Arena** - Prosecutor/Defender/Moderator agents challenge claims
3. **Graph-Based Consensus Network** - Trust-weighted voting with Byzantine fault tolerance

Key innovations: Dynamic agent spawning, adversarial verification, swarm bursts, memory mesh architecture.

## 📚 Essential Documents Map

### Strategic Documents
- **[docs/planning/milestones.md](./docs/planning/milestones.md)** - Comprehensive development milestones with team review schedule 🆕⭐
- **[docs/planning/original-plan.md](./docs/planning/original-plan.md)** - Original project vision and high-level plan
- **[docs/architecture/ARCHITECTURE_RECOMMENDATION.md](./docs/architecture/ARCHITECTURE_RECOMMENDATION.md)** - Detailed ECAMAN architecture specification ⭐
- **[consensus-roadmap.md](./consensus-roadmap.md)** - 12-week atomic task breakdown with success metrics ⭐
- **[STATUS.md](./STATUS.md)** - Current project status and progress tracking 🆕
- **[CHANGELOG.md](./CHANGELOG.md)** - Project history and version tracking 🆕

### Research & Background
- **[docs/research/agent-architectures-research.md](./docs/research/agent-architectures-research.md)** - Comprehensive research on cutting-edge agent architectures

### Development Resources
- **[README.md](./README.md)** - Public-facing project overview
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contribution guidelines
- **[DOCUMENTATION_STRUCTURE.md](./DOCUMENTATION_STRUCTURE.md)** - Documentation organization guide

## 🔑 Key Technical Decisions

### Tech Stack
- **Backend**: Python 3.11+, FastAPI, LangChain
- **LLMs**: GPT-4o-mini (primary), Ollama/Llama 3.2 (fallback)
- **Databases**: PostgreSQL + pgvector, Redis
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Infrastructure**: Docker, Digital Ocean droplet
- **Deployment**: GitHub Actions CI/CD (from Week 3!) 🆕

### Deployment Strategy 🆕
- **Week 3**: Early production deployment on DO
- **Continuous Deployment**: Every push to main goes live
- **Progressive Enhancement**: Add features to live system
- **Budget-conscious**: Start at $39/month, scale as needed

### Unique Features
1. **Dynamic Agent Spawning** - Meta-agent creates specialists on-demand
2. **Adversarial Debates** - Agents actively challenge each other
3. **Trust Networks** - Graph-based reputation system
4. **Swarm Bursts** - 10-20 micro-agents for urgent verifications
5. **Container-First Architecture** - All services run in Docker containers 🆕

### Development & Deployment Approach 🆕
- **Container-First**: Everything runs in Docker (local & prod)
- **No source code on production**: Only pre-built images from ghcr.io
- **CI/CD Pipeline**: GitHub Actions builds and deploys containers
- **Immutable Infrastructure**: Updates = new container versions

## 📊 Success Metrics

- **Technical**: 90%+ accuracy simple facts, <5s latency
- **Research**: 2+ papers, 1000+ GitHub stars
- **Adoption**: 100+ DAU within 3 months
- **LinkedIn**: Position as AI researcher through publications and demos

## 🚀 Current Phase & Next Steps

**Current**: Phase 1 - Foundation (Week 1 in progress)  
**Completed**:
- ✅ GitHub repository created and configured
- ✅ Documentation structure established
- ✅ GitHub Pages enabled
- ✅ Initial issues created (#1-#6)
- ✅ Project board set up
- ✅ Container-first architecture implemented
- ✅ Docker environment tested and working
- ✅ Basic FastAPI application running
- ✅ Python development environment setup (Issue #1)

**Next Immediate Tasks** (Priority Order):
1. Initialize database schema (Issue #2)
2. Implement BaseAgent class (Issue #3)
3. Create Meta-Agent orchestrator
4. Set up Redis for message queue

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

# Docker commands (main workflow)
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
docker-compose logs -f    # View logs
docker-compose ps         # Check status
docker-compose build      # Rebuild images

# Access services
# API: http://localhost:8000
# PostgreSQL: localhost:5433 (user: consensus, pass: devpassword)
# Redis: localhost:6380

# Development
source venv/bin/activate  # Activate virtual environment (if not using Docker)
pytest                    # Run tests
```

## 📝 Document Maintenance Notes

- **docs/planning/original-plan.md** - Original vision, keep as historical reference
- **docs/architecture/ARCHITECTURE_RECOMMENDATION.md** - Living document, update with implementation learnings
- **consensus-roadmap.md** - Update weekly with progress ⭐
- **STATUS.md** - Update after each milestone or weekly ⭐
- **CHANGELOG.md** - Update with significant changes
- **This file** - Update when major decisions or changes occur

---

*For quick status check, see STATUS.md. For deep technical details, start with docs/architecture/ARCHITECTURE_RECOMMENDATION.md. For implementation tasks, see consensus-roadmap.md.*

**Last Update**: 03.07.2025 13:55 CET - Container testing completed, documentation synchronized