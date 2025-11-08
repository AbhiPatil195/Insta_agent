# Run database migration
Write-Host "Running database migration..." -ForegroundColor Cyan

# Wait a bit for database to be ready
Start-Sleep -Seconds 3

# Copy migration file to container and run it
docker compose cp migrations/001_init.sql db:/tmp/001_init.sql
docker compose exec -T db psql -U postgres -d insta_agent -f /tmp/001_init.sql

Write-Host ""
Write-Host "✅ Migration completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Your bot is now ready to test!" -ForegroundColor Yellow
