# PowerShell script to update .env file
# NOTE: This is a template - update with your actual credentials
$envPath = "e:\Coding\Agents\Insta_Agent\.env"

# IMPORTANT: Replace these with your actual values
$GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"  # Get from console.groq.com
$POSTGRES_URL = "postgresql://postgres:postgres@db:5432/insta_agent"  # Or your Neon/Supabase URL

# Read the file
$content = Get-Content $envPath -Raw

# Update GROQ_API_KEY
$content = $content -replace 'GROQ_API_KEY=.*', "GROQ_API_KEY=$GROQ_API_KEY"

# Update LLM_PROVIDER
$content = $content -replace 'LLM_PROVIDER=none', 'LLM_PROVIDER=groq'

# Update POSTGRES_URL for local database
$content = $content -replace 'POSTGRES_URL=.*', "POSTGRES_URL=$POSTGRES_URL"

# Save the file
Set-Content -Path $envPath -Value $content

Write-Host "✅ .env file updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Updated:" -ForegroundColor Yellow
Write-Host "  - GROQ_API_KEY: Set"
Write-Host "  - LLM_PROVIDER: groq"
Write-Host "  - POSTGRES_URL: Local database"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run: docker compose down"
Write-Host "  2. Run: docker compose up -d --build"
Write-Host "  3. Run migration (after services start)"
