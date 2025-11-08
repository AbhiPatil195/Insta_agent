Param(
  [string]$Port = "8080"
)

Write-Host "Starting Cloudflare Tunnel to http://localhost:$Port ..."
Write-Host "Ensure cloudflared is installed: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"

try {
  $proc = Start-Process -FilePath "cloudflared" -ArgumentList @("tunnel","--url","http://localhost:$Port") -NoNewWindow -PassThru
  Write-Host "cloudflared started (pid: $($proc.Id)). Check its output for the public URL."
}
catch {
  Write-Error "Failed to start cloudflared. Make sure it's installed and in PATH."
}

