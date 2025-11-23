# PowerShell script to create GitHub repository and push README
# Make sure you have GitHub CLI (gh) installed: winget install --id GitHub.cli

Write-Host "Creating GitHub repository..." -ForegroundColor Green

# Create the repository
gh repo create hoodini/ctera-python-sdk `
    --public `
    --description "Python SDK for automating CTERA Global File System - Manage cloud storage, edge devices, and file operations programmatically" `
    --clone=false

if ($LASTEXITCODE -eq 0) {
    Write-Host "Repository created successfully!" -ForegroundColor Green
    
    # Initialize git if not already initialized
    if (-not (Test-Path ".git")) {
        Write-Host "Initializing git repository..." -ForegroundColor Yellow
        git init
        git branch -M main
    }
    
    # Copy the new README
    Write-Host "Setting up README..." -ForegroundColor Yellow
    Copy-Item "README_NEW.md" "README.md" -Force
    
    # Add remote if not exists
    $remoteExists = git remote | Select-String "origin"
    if (-not $remoteExists) {
        Write-Host "Adding remote origin..." -ForegroundColor Yellow
        git remote add origin "https://github.com/hoodini/ctera-python-sdk.git"
    } else {
        Write-Host "Updating remote origin..." -ForegroundColor Yellow
        git remote set-url origin "https://github.com/hoodini/ctera-python-sdk.git"
    }
    
    # Stage and commit
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git add .
    git commit -m "Initial commit: Add comprehensive README documentation

- Add detailed README explaining CTERA Python SDK architecture
- Document core, edge, async, and direct modules
- Include quick start examples and common use cases
- Add installation instructions and best practices
- Provide clear learning path for new users"
    
    # Push to GitHub
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    Write-Host "`nRepository setup complete!" -ForegroundColor Green
    Write-Host "View your repository at: https://github.com/hoodini/ctera-python-sdk" -ForegroundColor Cyan
    
} else {
    Write-Host "Failed to create repository. Please check your GitHub CLI authentication." -ForegroundColor Red
    Write-Host "Run 'gh auth login' to authenticate." -ForegroundColor Yellow
}

