#!/bin/bash
# GitHub Setup Script for ConsensusNet
# This script configures GitHub Pages and Projects after the repo is pushed

echo "🚀 ConsensusNet GitHub Configuration Script"
echo "=========================================="
echo ""

# Check if we're in a git repo
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository!"
    exit 1
fi

echo "📋 This script will configure:"
echo "- GitHub Pages for documentation"
echo "- GitHub Projects for roadmap tracking"
echo "- Repository settings"
echo ""

# First, check authentication
echo "🔐 Step 1: Checking GitHub authentication..."
echo ""
echo "Please make sure you're authenticated with GitHub."
echo "You can use one of these methods:"
echo ""
echo "Option A - Personal Access Token (recommended):"
echo "  1. Go to: https://github.com/settings/tokens/new"
echo "  2. Create token with 'repo' scope"
echo "  3. Use token as password when pushing"
echo ""
echo "Option B - SSH Key:"
echo "  1. Check if you have SSH key: ls ~/.ssh/id_*.pub"
echo "  2. If not, generate: ssh-keygen -t ed25519 -C 'your_email@example.com'"
echo "  3. Add to GitHub: https://github.com/settings/ssh/new"
echo ""
echo "Option C - GitHub CLI:"
echo "  1. Install: brew install gh"
echo "  2. Login: gh auth login"
echo ""
read -p "Press Enter when you're ready to continue..."

# Push to GitHub
echo ""
echo "📤 Step 2: Pushing to GitHub..."
echo "Trying to push your code..."
echo ""

# Try with current remote
git push -u origin main

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Push failed. Let's fix this:"
    echo ""
    echo "Try these commands based on your auth method:"
    echo ""
    echo "For Personal Access Token:"
    echo "  git remote set-url origin https://hretheum@github.com/hretheum/consensus.net.git"
    echo "  git push -u origin main"
    echo "  (use your token as password)"
    echo ""
    echo "For SSH (after adding key to GitHub):"
    echo "  git remote set-url origin git@github.com:hretheum/consensus.net.git"
    echo "  git push -u origin main"
    echo ""
    echo "For GitHub CLI:"
    echo "  gh repo clone hretheum/consensus.net temp_clone"
    echo "  cp -r ./* temp_clone/"
    echo "  cd temp_clone && git add . && git commit -m 'Initial commit' && git push"
    echo ""
    exit 1
fi

echo "✅ Code pushed successfully!"
echo ""

# Configure GitHub Pages
echo "📄 Step 3: Configuring GitHub Pages..."
echo ""
echo "After push succeeds, configure Pages manually:"
echo "1. Go to: https://github.com/hretheum/consensus.net/settings/pages"
echo "2. Source: Deploy from a branch"
echo "3. Branch: main"
echo "4. Folder: /docs"
echo "5. Click Save"
echo ""
echo "Or use GitHub CLI (if installed):"
echo "  gh api repos/hretheum/consensus.net/pages -X POST -f source='branch' -f source[branch]='main' -f source[path]='/docs'"
echo ""

# Configure GitHub Projects
echo "📊 Step 4: Setting up GitHub Projects..."
echo ""
echo "Create a project board for roadmap tracking:"
echo "1. Go to: https://github.com/hretheum/consensus.net/projects/new"
echo "2. Template: 'Basic kanban'"
echo "3. Project name: 'ConsensusNet Roadmap'"
echo "4. Description: '12-week development roadmap for ConsensusNet'"
echo ""
echo "Or use GitHub CLI:"
echo "  gh project create --title 'ConsensusNet Roadmap' --body '12-week development roadmap'"
echo ""

# Create initial issues
echo "📝 Step 5: Creating initial issues..."
echo ""
echo "Run these commands to create starter issues:"
echo ""
cat << 'EOF'
# Phase 0 Issues
gh issue create --title "Setup Development Environment" --body "- Create virtual environment
- Install dependencies
- Configure IDE
- Setup pre-commit hooks" --label "setup,phase-0"

gh issue create --title "Initialize Database Schema" --body "- Design core tables
- Create migration files
- Setup Alembic
- Test with PostgreSQL" --label "database,phase-0"

# Phase 1 Issues
gh issue create --title "Implement BaseAgent Abstract Class" --body "- Define agent interface
- Create verification result model
- Add error handling
- Write unit tests" --label "agent,phase-1"

gh issue create --title "Create Simple Fact Checker Agent" --body "- Implement basic verification logic
- Integrate with LLM
- Add confidence scoring
- Test with known facts" --label "agent,phase-1"

gh issue create --title "Build FastAPI Gateway" --body "- Setup FastAPI structure
- Create /verify endpoint
- Add request validation
- Implement rate limiting" --label "api,phase-1"
EOF

echo ""
echo "✅ Setup instructions complete!"
echo ""
echo "📌 Repository Quick Links:"
echo "- Home: https://github.com/hretheum/consensus.net"
echo "- Issues: https://github.com/hretheum/consensus.net/issues"
echo "- Projects: https://github.com/hretheum/consensus.net/projects"
echo "- Wiki: https://github.com/hretheum/consensus.net/wiki"
echo "- Settings: https://github.com/hretheum/consensus.net/settings"
echo ""
echo "🎉 Good luck with ConsensusNet!"
