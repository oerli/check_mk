# powershell get horizon status
# 30.05.2018 by Roland Mueller
# VMWare PowerCLI needed

Import-Module VMware.VimAutomation.HorizonView

$hzUser = ""
$hzPass = ""
$hzDomain = ""
$hzConn = ""
$hvServer = Connect-HVServer -server $hzConn -User $hzUser -Password $hzPass -Domain $hzDomain
$hvServices = $Global:DefaultHVServers.ExtensionData

$query_service = New-Object "Vmware.Hv.QueryServiceService"
$query = New-Object "Vmware.Hv.QueryDefinition"
$query.queryEntityType = 'DesktopSummaryView'

$hvPools = $query_service.QueryService_Query($hvServices,$query)
# desktop-pool, 
Write-Host '<<<horizon_status>>>'   
#$hvPools.Results.DesktopSummaryData | Format-Table -HideTableHeaders
foreach ($pool in $hvPools.Results.DesktopSummaryData) {
    Write-Host($pool.name + ' ' + $pool.enabled + ' ' + $pool.ProvisioningEnabled + ' ' + $pool.NumMachines + ' ' + $pool.NumSessions )
}