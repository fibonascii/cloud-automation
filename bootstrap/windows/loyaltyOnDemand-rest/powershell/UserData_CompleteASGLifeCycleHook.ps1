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
Write-Output "$(Get-Date -format T) - Updating LifeCycleHook to COMPLETE"
$instanceId = Invoke-RestMethod -uri http://169.254.169.254/latest/meta-data/instance-id
$ClientCode = (Get-EC2Tag -Filter @{ Name="key";Values="ClientCode"},@{Name="resource-id";Values=$instanceId}).Value
Complete-ASLifecycleAction -InstanceId $instanceId -LifecycleHookName "$($ClientCode)-REST-API-LCH" -AutoScalingGroupName "1" -LifecycleActionResult "CONTINUE"
Write-Output "$(Get-Date -format T) - LifeCycleHook to COMPLETED!"
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
