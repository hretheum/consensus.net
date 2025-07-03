#!/bin/bash
# ConsensusNet Documentation Reorganization Script
# Run this script to organize documentation according to DOCUMENTATION_STRUCTURE.md

echo "🚀 Starting ConsensusNet documentation reorganization..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p docs/{architecture,research,planning,development,api,operations}
mkdir -p decisions
mkdir -p meeting-notes
mkdir -p docs/research/paper-drafts

# Move and rename existing files
echo "📄 Moving existing documents..."

# Move ARCHITECTURE_RECOMMENDATION.md
if [ -f "ARCHITECTURE_RECOMMENDATION.md" ]; then
    mv ARCHITECTURE_RECOMMENDATION.md docs/architecture/
    echo "  ✓ Moved ARCHITECTURE_RECOMMENDATION.md"
fi

# Rename and move compass artifact
if [ -f "compass_artifact_wf-472e5d77-9925-4942-945f-84e0686dc6f0_text_markdown.md" ]; then
    mv compass_artifact_wf-472e5d77-9925-4942-945f-84e0686dc6f0_text_markdown.md docs/research/agent-architectures-research.md
    echo "  ✓ Renamed and moved agent architectures research"
fi

# Move consensusnet-plan.md
if [ -f "consensusnet-plan.md" ]; then
    mv consensusnet-plan.md docs/planning/original-plan.md
    echo "  ✓ Moved original plan"
fi

# Create README.md if it doesn't exist
if [ ! -f "README.md" ]; then
    echo "📝 Creating README.md..."
    cat > README.md << 'EOF'
# ConsensusNet

> Revolutionary multi-agent AI system for decentralized fact-checking using collective intelligence

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

ConsensusNet is an innovative multi-agent AI system that leverages collective intelligence to combat misinformation. By orchestrating specialized AI agents in adversarial debates and consensus mechanisms, it achieves unprecedented accuracy in fact-checking.

## ✨ Key Features

- **Dynamic Agent Spawning**: Meta-agents create specialized verifiers on-demand
- **Adversarial Verification**: Prosecutor/Defender agents actively challenge claims  
- **Byzantine Fault Tolerance**: Robust consensus even with unreliable agents
- **Trust Networks**: Graph-based reputation system for agent credibility
- **Real-time Processing**: WebSocket support for live verification updates

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/[username]/consensusnet
cd consensusnet

# Run setup script
./scripts/setup.sh

# Start development server
docker-compose up -d
python src/main.py
```

## 📚 Documentation

- [Architecture Overview](docs/architecture/ARCHITECTURE_RECOMMENDATION.md)
- [Development Setup](docs/development/setup-guide.md)
- [API Reference](docs/api/api-design.md)
- [Research Background](docs/research/agent-architectures-research.md)

## 🏗️ Architecture

ConsensusNet implements ECAMAN (Emergent Consensus through Adversarial Meta-Agent Networks):

```
Meta-Agent Orchestrator
    ↓ spawns
Specialized Agents → Adversarial Debates → Trust-Weighted Consensus
```

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
EOF
    echo "  ✓ Created README.md"
fi

# Create basic .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Logs
*.log

# Database
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db

# Project specific
/data/
/models/
/outputs/
EOF
    echo "  ✓ Created .gitignore"
fi

echo ""
echo "✅ Documentation reorganization complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review the new structure in docs/"
echo "2. Update any broken links in documents"
echo "3. Create missing high-priority documents"
echo "4. Commit changes to git"
echo ""
echo "Run 'tree docs/' to see the new structure"
