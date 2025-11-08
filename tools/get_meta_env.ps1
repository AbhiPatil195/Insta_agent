<#
  Helper to fetch Meta Page ID, Page Access Token, and IG Business ID.
  Run this locally in PowerShell. It does NOT save secrets; it only prints values.

  Prereqs:
  - Your Instagram Business/Creator account is linked to your Facebook Page.
  - You have a short-lived User Access Token with scopes:
    pages_show_list,pages_manage_metadata,pages_read_engagement,pages_messaging,instagram_manage_messages,instagram_basic
    Easiest: Graph API Explorer → Select your app → Add the permissions above → Generate Access Token.

  Usage:
    1) Run:  pwsh -File tools/get_meta_env.ps1
    2) Paste your App ID, App Secret, and User Token when prompted.
    3) Pick your Page from the list; the script prints .env lines.
#>

param(
  [string]$AppId,
  [string]$AppSecret,
  [string]$UserToken
)

function Read-IfEmpty($value, $prompt) {
  if ([string]::IsNullOrWhiteSpace($value)) {
    return Read-Host $prompt
  }
  return $value
}

try {
  $AppId    = Read-IfEmpty $AppId    "Enter App ID"
  $AppSecret= Read-IfEmpty $AppSecret"Enter App Secret (will echo)"
  $UserToken= Read-IfEmpty $UserToken"Paste short-lived User Access Token"

  Write-Host "Exchanging for long-lived User token..." -ForegroundColor Cyan
  $oauthUrl = "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=$AppId&client_secret=$AppSecret&fb_exchange_token=$UserToken"
  $oauthRes = Invoke-RestMethod -Method Get -Uri $oauthUrl
  $LongUserToken = $oauthRes.access_token
  if (-not $LongUserToken) { throw "Failed to exchange token. Response: $($oauthRes | ConvertTo-Json -Depth 5)" }

  Write-Host "Listing pages for your account..." -ForegroundColor Cyan
  $pagesRes = Invoke-RestMethod -Method Get -Uri "https://graph.facebook.com/v21.0/me/accounts?access_token=$LongUserToken"
  if (-not $pagesRes.data -or $pagesRes.data.Count -eq 0) { throw "No pages found for this user/token." }

  $i = 0
  foreach ($p in $pagesRes.data) {
    Write-Host ("[{0}] {1} (ID: {2})" -f $i, $p.name, $p.id)
    $i++
  }
  $idx = Read-Host "Pick a page number"
  if ($idx -notmatch '^[0-9]+$' -or [int]$idx -ge $pagesRes.data.Count) { throw "Invalid selection." }
  $page = $pagesRes.data[[int]$idx]
  $PAGE_ID = $page.id
  $PAGE_TOKEN = $page.access_token

  Write-Host "Fetching Instagram Business Account ID..." -ForegroundColor Cyan
  $igRes = Invoke-RestMethod -Method Get -Uri "https://graph.facebook.com/v21.0/$PAGE_ID?fields=instagram_business_account&access_token=$PAGE_TOKEN"
  $IG_BIZ_ID = $igRes.instagram_business_account.id
  if (-not $IG_BIZ_ID) { Write-Warning "No instagram_business_account linked to this page. Link IG to the Page and retry." }

  Write-Host ""; Write-Host "Add these to your .env:" -ForegroundColor Green
  Write-Host ("META_PAGE_ID={0}" -f $PAGE_ID)
  Write-Host ("META_PAGE_ACCESS_TOKEN={0}" -f $PAGE_TOKEN)
  if ($IG_BIZ_ID) { Write-Host ("META_IG_BUSINESS_ID={0}" -f $IG_BIZ_ID) }

  Write-Host ""; Write-Host "Tip: Use Access Token Debugger to extend User token if needed, then re-run to refresh Page token." -ForegroundColor DarkGray
}
catch {
  Write-Error $_
  if ($_.Exception.Response) {
    try { $body = ($_ .Exception.Response.GetResponseStream()); $reader = New-Object System.IO.StreamReader($body); Write-Host ($reader.ReadToEnd()) } catch {}
  }
  exit 1
}

