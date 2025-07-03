#!/bin/bash
# Git push helper with authentication

source .env

# Temporarily set remote with PAT
git remote set-url origin https://hretheum:$GITHUB_TOKEN@github.com/hretheum/consensus.net.git

# Push changes
git push "$@"

# Remove PAT from remote for security
git remote set-url origin https://github.com/hretheum/consensus.net.git

echo "✅ Push completed and PAT removed from remote URL"
