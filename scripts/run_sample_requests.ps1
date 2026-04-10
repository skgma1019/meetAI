$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

$baseUrl = "http://127.0.0.1:8000"

function Show-Section {
  param(
    [string]$Title,
    [string]$Method,
    [string]$Url,
    [string]$BodyPath = ""
  )

  Write-Host ""
  Write-Host "== $Title =="

  if ($Method -eq "GET") {
    $response = Invoke-RestMethod -Uri $Url -Method Get
  } else {
    $response = Invoke-RestMethod -Uri $Url -Method Post -ContentType "application/json; charset=utf-8" -InFile $BodyPath
  }

  $response | ConvertTo-Json -Depth 8
}

Show-Section -Title "health" -Method "GET" -Url "$baseUrl/health"
Show-Section -Title "analyze/language" -Method "POST" -Url "$baseUrl/analyze/language" -BodyPath "G:\meetAI\data\samples\language_request.json"
Show-Section -Title "analyze/nonverbal" -Method "POST" -Url "$baseUrl/analyze/nonverbal" -BodyPath "G:\meetAI\data\samples\nonverbal_request.json"
Show-Section -Title "analyze/full" -Method "POST" -Url "$baseUrl/analyze/full" -BodyPath "G:\meetAI\data\samples\full_request.json"
