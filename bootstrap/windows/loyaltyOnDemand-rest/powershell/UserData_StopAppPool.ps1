Function SafeStopAppPool ([string] $webSiteName) {
[bool] $Return = $False
$IISPath = "IIS:\Sites\$webSiteName"
$webSite = get-website | where-object { $_.name -eq $webSiteName }
if ($webSite)
{
if((Get-WebAppPoolState -Name $webSiteName).Value -ne 'Stopped'){
   
    Stop-WebAppPool -Name $webSiteName
    Write-Output "$(Get-Date -format T) - Stopping IIS AppPool: $webSiteName"
    do
{
    Write-Host (Get-WebAppPoolState $webSiteName).Value
    Start-Sleep -Seconds 1
}
until ( (Get-WebAppPoolState -Name $webSiteName).Value -eq "Stopped" )
}
else
{
Write-Output "$(Get-Date -format T) - IIS AppPool already stopped: $webSiteName"
} 
}
else
{
 Write-Output "$(Get-Date -format T) - IIS AppPool does not exist: $webSiteName"
}
}


###Create Log transcript
$logFolder = "$env:SystemRoot\Temp\"
$scriptName = ([io.fileinfo]$MyInvocation.MyCommand.Definition).BaseName
$timeStamp = Get-Date -format MMddyyyHHmmss
$scriptLogFile = ($logFolder + $scriptName + "-" + $timeStamp + "-script.log")
Start-Transcript -Path $scriptLogFile | out-null
##End Log transcript

##Event Log
$eventLogSource = ([io.fileinfo]$MyInvocation.MyCommand.Definition).BaseName
$logFileExists = ([System.Diagnostics.EventLog]::Exists('ConfigurationManagement') -And [System.Diagnostics.EventLog]::SourceExists($eventLogSource))
if (!$logFileExists) {
$eventLogParameters = @{
    LogName = 'ConfigurationManagement'
    Source = $eventLogSource
}
New-EventLog @eventLogParameters
}
##End Event Log Setup

Try
{
Write-Output "$(Get-Date -format T) - Retrieving Input Parameters"
$instanceId = Invoke-RestMethod -uri http://169.254.169.254/latest/meta-data/instance-id
$ClientCode = (Get-EC2Tag -Filter @{ Name="key";Values="ClientCode"},@{Name="resource-id";Values=$instanceId}).Value
SafeStopAppPool("Rest API")
Write-Output "$(Get-Date -format T) - Stopped IIS AppPool: Rest API"
}
Catch
{
Write-Output "$(Get-Date -format T) - Exception Caught: $_ "
}
Finally
{
##Write Transcript Log
Stop-Transcript | out-null
##Write to Event Log
$LogMessage = [IO.File]::ReadAllText($scriptLogFile)
$eventLogMessageParameters = @{
    LogName ='ConfigurationManagement'
    Source = $eventLogSource
    EventId ='100'
    EntryType = 'Information'
    Message =$LogMessage}
    Write-EventLog @eventLogMessageParameters
##End Write Event Log
}
