#!/bin/bash
# Configure GitHub features using API directly

source .env

echo "🚀 Configuring GitHub features for ConsensusNet..."
echo ""

# 1. Configure GitHub Pages
echo "📄 Setting up GitHub Pages..."
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO/pages \
  -d '{"source":{"branch":"main","path":"/docs"}}'

echo ""
echo ""

# 2. Update repository description and topics
echo "📝 Updating repository settings..."
curl -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO \
  -d '{
    "description": "Revolutionary multi-agent AI system for decentralized fact-checking using collective intelligence",
    "homepage": "https://hretheum.github.io/consensus.net",
    "topics": ["ai", "multi-agent-systems", "fact-checking", "machine-learning", "consensus-algorithms", "python", "langchain", "research"],
    "has_issues": true,
    "has_projects": true,
    "has_wiki": true
  }'

echo ""
echo ""

# 3. Create a project board
echo "📊 Creating project board..."
PROJECT_RESPONSE=$(curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.inertia-preview+json" \
  https://api.github.com/repos/$GITHUB_REPO/projects \
  -d '{
    "name": "ConsensusNet Roadmap",
    "body": "12-week development roadmap for ConsensusNet multi-agent fact-checking system"
  }')

echo ""
echo ""

# 4. Create initial issues
echo "📋 Creating initial issues..."

# Issue 1: Setup Development Environment
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO/issues \
  -d '{
    "title": "Setup Development Environment",
    "body": "## Phase 0 - Week 0\n\n- [ ] Create virtual environment\n- [ ] Install dependencies\n- [ ] Configure IDE\n- [ ] Setup pre-commit hooks\n\n**Success Metric**: Development environment reproducible in <30 minutes\n\nSee: [consensus-roadmap.md](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md#01-development-environment-setup)",
    "labels": ["setup", "phase-0", "priority-high"]
  }'

echo ""

# Issue 2: Initialize Database Schema
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO/issues \
  -d '{
    "title": "Initialize Database Schema",
    "body": "## Phase 0 - Week 0\n\n- [ ] Design core tables\n- [ ] Create migration files\n- [ ] Setup Alembic\n- [ ] Test with PostgreSQL\n\n**Success Metric**: Schema can be applied to fresh PostgreSQL instance\n\nSee: [consensus-roadmap.md](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md#02-infrastructure-planning)",
    "labels": ["database", "phase-0", "backend"]
  }'

echo ""

# Issue 3: Implement BaseAgent Class
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO/issues \
  -d '{
    "title": "Implement BaseAgent Abstract Class",
    "body": "## Phase 1 - Sprint 1\n\n- [ ] Define agent interface\n- [ ] Create VerificationResult model\n- [ ] Add error handling\n- [ ] Write unit tests\n\n**Success Metric**: 100% test coverage for base class\n\nSee: [consensus-roadmap.md](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md#11-base-agent-architecture)",
    "labels": ["agent", "phase-1", "architecture"]
  }'

echo ""

# Issue 4: Create Simple Fact Checker
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO/issues \
  -d '{
    "title": "Create Simple Fact Checker Agent",
    "body": "## Phase 1 - Sprint 1\n\n- [ ] Implement basic verification logic\n- [ ] Integrate with LLM (GPT-4o-mini)\n- [ ] Add confidence scoring\n- [ ] Test with known facts\n\n**Success Metric**: Verifies basic factual claims with 70%+ accuracy\n\nSee: [consensus-roadmap.md](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md#12-simple-verification-agent)",
    "labels": ["agent", "phase-1", "priority-high"]
  }'

echo ""

# Issue 5: Build FastAPI Gateway
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$GITHUB_REPO/issues \
  -d '{
    "title": "Build FastAPI Gateway",
    "body": "## Phase 1 - Sprint 1\n\n- [ ] Setup FastAPI structure\n- [ ] Create /verify endpoint\n- [ ] Add request validation\n- [ ] Implement rate limiting\n\n**Success Metric**: API starts and serves OpenAPI docs at /docs\n\nSee: [consensus-roadmap.md](https://github.com/hretheum/consensus.net/blob/main/consensus-roadmap.md#13-basic-api-layer)",
    "labels": ["api", "phase-1", "backend"]
  }'

echo ""
echo ""
echo "✅ GitHub features configured!"
echo ""
echo "📌 Quick Links:"
echo "- Repository: https://github.com/$GITHUB_REPO"
echo "- GitHub Pages: https://hretheum.github.io/consensus.net (may take a few minutes)"
echo "- Issues: https://github.com/$GITHUB_REPO/issues"
echo "- Projects: https://github.com/$GITHUB_REPO/projects"
echo ""
echo "🎉 ConsensusNet is now live on GitHub!"
