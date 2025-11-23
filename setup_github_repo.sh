#!/bin/bash
# Bash script to create GitHub repository and push README
# Make sure you have GitHub CLI (gh) installed: brew install gh

echo "Creating GitHub repository..."

# Create the repository
gh repo create hoodini/ctera-python-sdk \
    --public \
    --description "Python SDK for automating CTERA Global File System - Manage cloud storage, edge devices, and file operations programmatically" \
    --clone=false

if [ $? -eq 0 ]; then
    echo "Repository created successfully!"
    
    # Initialize git if not already initialized
    if [ ! -d ".git" ]; then
        echo "Initializing git repository..."
        git init
        git branch -M main
    fi
    
    # Copy the new README
    echo "Setting up README..."
    cp README_NEW.md README.md
    
    # Add remote if not exists
    if ! git remote | grep -q "origin"; then
        echo "Adding remote origin..."
        git remote add origin "https://github.com/hoodini/ctera-python-sdk.git"
    else
        echo "Updating remote origin..."
        git remote set-url origin "https://github.com/hoodini/ctera-python-sdk.git"
    fi
    
    # Stage and commit
    echo "Committing changes..."
    git add .
    git commit -m "Initial commit: Add comprehensive README documentation

- Add detailed README explaining CTERA Python SDK architecture
- Document core, edge, async, and direct modules
- Include quick start examples and common use cases
- Add installation instructions and best practices
- Provide clear learning path for new users"
    
    # Push to GitHub
    echo "Pushing to GitHub..."
    git push -u origin main
    
    echo ""
    echo "Repository setup complete!"
    echo "View your repository at: https://github.com/hoodini/ctera-python-sdk"
    
else
    echo "Failed to create repository. Please check your GitHub CLI authentication."
    echo "Run 'gh auth login' to authenticate."
fi

