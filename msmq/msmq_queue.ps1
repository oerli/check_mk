write-host "<<<msmq_queue>>>"
get-msmqqueue | Foreach-Object { Write-Host ($_.QueueName -replace ".*\\", "" -replace " ", "_") $_.MessageCount}