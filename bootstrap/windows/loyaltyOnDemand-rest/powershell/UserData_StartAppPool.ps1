Function SafeStartAppPool ([string] $webSiteName) {
$IISPath = "IIS:\Sites\$webSiteName"
$webSite = get-website | where-object { $_.name -eq $webSiteName }
if ($webSite)
{
if((Get-WebAppPoolState -Name $webSiteName).Value -ne 'Started'){

$appPoolStart = $False
$elapsed = [System.Diagnostics.Stopwatch]::StartNew()
$timeout = new-timespan -Minutes 1
Do {
    Try
    {
    Start-WebAppPool -Name $webSiteName
        do
{
    Write-Host (Get-WebAppPoolState $webSiteName).Value
    Start-Sleep -Seconds 1
}
until ( (Get-WebAppPoolState -Name $webSiteName).Value -eq "Started" )
    }
    Catch
    {

    }

if ((Get-WebAppPoolState -Name "Rest API").Value -eq 'Started')
{
break
}
else
{
sleep 15
}
} # End of 'Do' 
While ($elapsed.Elapsed -lt $timeout)
if ((Get-WebAppPoolState -Name "Rest API").Value -ne 'Started')
{
throw "Could not start AppPool in alotted time"
}

}
else
{
Write-Output "$(Get-Date -format T) - IIS AppPool already Started: $webSiteName"
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
SafeStartAppPool("Rest API")
Write-Output "$(Get-Date -format T) - Started IIS AppPool: Rest API"
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
