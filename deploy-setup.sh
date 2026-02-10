#!/bin/bash

echo "=== GitHub Setup Script ==="
echo ""
echo "Make sure you have created a repository on GitHub first!"
echo "Repository name: ca-crm"
echo ""
read -p "Enter your GitHub username: " username
echo ""

git init
git add .
git commit -m "Initial commit - CA CRM System"
git branch -M main
git remote add origin https://github.com/$username/ca-crm.git
git push -u origin main

echo ""
echo "✅ Code pushed to GitHub!"
echo "Next: Follow DEPLOYMENT.md to deploy on Render"
