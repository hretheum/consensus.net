# Changelog

All notable changes to ConsensusNet project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Week 0 - 2025-07-03

#### Added
- Initial project structure and documentation
- Complete documentation hierarchy in `/docs`
- GitHub repository at https://github.com/hretheum/consensus.net
- GitHub Pages documentation site
- MIT License
- Contributing guidelines
- 12-week development roadmap with atomic tasks
- ECAMAN architecture specification
- Research on cutting-edge agent architectures
- Project context file for AI assistants
- Status tracking document
- 5 initial GitHub issues (#1-#5)
- GitHub Projects board for roadmap visualization
- Container-first architecture design ✨
- Docker configuration files:
  - `Dockerfile.api` for API service
  - `docker-compose.yml` for development
  - `docker-compose.prod.yml.example` for production
  - `.dockerignore` for optimized builds
- GitHub Actions CI/CD pipeline (`.github/workflows/deploy.yml`)
- Basic FastAPI application with health checks
- Python dependencies in `requirements.txt`
- Early deployment strategy for Week 3

#### Changed
- Port configuration to avoid conflicts:
  - PostgreSQL: 5433 (from default 5432)
  - Redis: 6380 (from default 6379)

#### Tested
- Docker containerization working correctly
- All services (API, PostgreSQL, Redis) running in containers
- Hot reload for development confirmed
- Health check endpoints operational
  - `.dockerignore` for build optimization
- Early deployment strategy (Week 3) with CI/CD pipeline
- Helper scripts:
  - `reorganize_docs.sh` - Documentation structure setup
  - `configure_github.sh` - GitHub features configuration
  - `git-push.sh` - Secure push with PAT

#### Changed
- Updated roadmap with container-first tasks
- Modified deployment approach to use GitHub Container Registry
- No source code on production servers policy

#### Architecture Decisions
- Container-first approach for all services
- GitHub Container Registry (ghcr.io) for image storage
- Managed PostgreSQL on Digital Ocean (not containerized)
- Immutable infrastructure pattern

#### Security
- `.env` file for GitHub PAT (added to .gitignore)
- Secure git push helper that removes PAT from remote URL

#### Documentation
- README with project overview and badges
- CONTRIBUTING.md with contribution guidelines
- STATUS.md for quick project status overview
- Comprehensive roadmap with success metrics
- Architecture recommendation document

### Pre-Project Research - 2025-07-01 to 2025-07-02

#### Added
- Initial ConsensusNet concept
- Research on multi-agent architectures
- Feasibility analysis for fact-checking system
- Budget planning for Digital Ocean deployment

---

## Versioning Scheme

- **0.0.x** - Pre-development phase (documentation, planning)
- **0.1.x** - Phase 1: Foundation (single agent)
- **0.2.x** - Phase 2: Multi-agent system
- **0.3.x** - Phase 3: Advanced consensus
- **0.4.x** - Phase 4: Production readiness
- **1.0.0** - First stable release

Next milestone: **v0.1.0** - Working single agent system