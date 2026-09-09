for ($i = 1; $i -le 3; $i++) {
    Write-Host "Test Run $i"
    curl.exe -X POST https://smart-plant-health-monitoring-using.vercel.app/api/gemini -H "Content-Type: application/json" -d "@payload.json"
    Write-Host "`n---"
    Start-Sleep -Seconds 5
}
