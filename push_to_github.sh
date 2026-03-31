#!/bin/bash
# Push to GitHub — run this after setting up a PAT with 'contents:write' scope
# or after authenticating with: gh auth login
set -e

cd "$(dirname "$0")"

echo "Pushing equi-content-engine to ryanpershad-cmd/Equi-Project..."

# Ensure remote is set
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/ryanpershad-cmd/Equi-Project.git

# Push
git push -u origin main

echo "✅ Pushed successfully to https://github.com/ryanpershad-cmd/Equi-Project"
