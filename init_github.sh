#!/bin/bash
# Initialize Git and push to GitHub for ConsensusNet project

echo "🚀 Initializing ConsensusNet repository..."
echo "Repository: https://github.com/hretheum/consensus.net"
echo ""

# Check if we're in the right directory
if [ ! -f "project_context.md" ]; then
    echo "❌ Error: Not in ConsensusNet directory!"
    echo "Please run this script from /Users/hretheum/dev/bezrobocie/consenus"
    exit 1
fi

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "  ✓ Git initialized"
else
    echo "  ℹ️  Git already initialized"
fi

# Add remote if not already added
if ! git remote | grep -q "origin"; then
    echo "🔗 Adding GitHub remote..."
    git remote add origin https://github.com/hretheum/consensus.net.git
    echo "  ✓ Remote added"
else
    echo "  ℹ️  Remote already exists"
fi

# Create initial commit
echo ""
echo "📝 Creating initial commit..."
git add .
git commit -m "Initial commit: ConsensusNet - Multi-agent AI fact-checking system

- Complete documentation structure
- ECAMAN architecture specification
- 12-week development roadmap
- Research background on agent architectures
- Project setup and configuration files"

# Set main branch
git branch -M main

# Push to GitHub
echo ""
echo "⬆️  Pushing to GitHub..."
echo "You may be prompted for your GitHub credentials."
echo ""
git push -u origin main

echo ""
echo "✅ Repository successfully initialized and pushed!"
echo ""
echo "🎉 Your project is now live at: https://github.com/hretheum/consensus.net"
echo ""
echo "📋 Next steps:"
echo "1. Add a LICENSE file (MIT recommended)"
echo "2. Set up GitHub Issues for task tracking"
echo "3. Configure GitHub Actions for CI/CD"
echo "4. Add collaborators if working with a team"
echo "5. Create a project board for roadmap visualization"
echo ""
echo "🔗 Quick links:"
echo "- Repository: https://github.com/hretheum/consensus.net"
echo "- Issues: https://github.com/hretheum/consensus.net/issues"
echo "- Projects: https://github.com/hretheum/consensus.net/projects"
