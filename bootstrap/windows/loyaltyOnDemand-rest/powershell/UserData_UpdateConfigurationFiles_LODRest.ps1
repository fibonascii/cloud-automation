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


$restApiPrefix = (Get-SSMParameterValue -Names $ClientCode-restApiPrefix -WithDecryption $true).Parameters[0].Value
Write-Host "Rest API Prefix =" $restApiPrefix 
$restKongEndpoint = (Get-SSMParameterValue -Names $ClientCode-restKongEndpoint -WithDecryption $true).Parameters[0].Value
Write-Host "Rest Kong Endpoint =" $restKongEndpoint 
$restKongProvisionKey = (Get-SSMParameterValue -Names $ClientCode-restKongProvisionKey -WithDecryption $true).Parameters[0].Value
Write-Host "Rest Kong Provision Key =" $restKongProvisionKey 
$loyaltyWareOrganization = (Get-SSMParameterValue -Names $ClientCode-loyaltyWareOrganization -WithDecryption $true).Parameters[0].Value
Write-Host "LoyaltyWare Organization =" $loyaltyWareOrganization 
$loyaltyWareEnvironment = (Get-SSMParameterValue -Names $ClientCode-loyaltyWareEnvironment -WithDecryption $true).Parameters[0].Value
Write-Host "LoyaltyWare Environment =" $loyaltyWareEnvironment 

Write-Output "$(Get-Date -format T) - Input Parameters Received!"

Write-Output "$(Get-Date -format T) - Editing AppSettings.Json"
$appSettingsJsonPath = 'C:\inetpub\wwwroot\loyaltyware-rest\appsettings.json'
$appSettingsJson = Get-Content $appSettingsJsonPath  -raw | ConvertFrom-Json
$appSettingsJson.AppSettings.ApiName = $restApiPrefix
$appSettingsJson.AppSettings.KongSettings.KongIpAddress = $restKongEndpoint
$appSettingsJson.AppSettings.KongSettings.ProvisionKey = $restKongProvisionKey
$appSettingsJson | ConvertTo-Json -Depth 10| set-content $appSettingsJsonPath

Write-Output "$(Get-Date -format T) - Successfully Edited AppSettings.Json"

Write-Output "$(Get-Date -format T) - Updating Brierley Framework WebApi Configuration File to Set Loyalty Ware Configuration."
$brierleyFrameworkWebApiConfigFilePath = 'C:\inetpub\wwwroot\loyaltyware-rest\Brierley.LoyaltyWare.WebApi.exe.config'
$brierleyFrameworkWebApiConfigFileObject = (Get-Content $brierleyFrameworkWebApiConfigFilePath) -as [Xml]

$lwOrganizationObject = $brierleyFrameworkWebApiConfigFileObject.configuration.appSettings.add | where {$_.key -eq 'LWOrganization'}
$lwOrganizationObject.value = $loyaltyWareOrganization

$lwEnvironmentObject = $brierleyFrameworkWebApiConfigFileObject.configuration.appSettings.add | where {$_.key -eq 'LWEnvironment'}
$lwEnvironmentObject.value = $loyaltyWareEnvironment

$lwConfigObject = $brierleyFrameworkWebApiConfigFileObject.configuration.appSettings.add | where {$_.key -eq 'LWConfig'}
$lwConfigObject.value = "C:\inetpub\wwwroot\LWConfig"

$lwAssemblyPathObject = $brierleyFrameworkWebApiConfigFileObject.configuration.appSettings.add | where {$_.key -eq 'LWAssemblyPath'}
$lwAssemblyPathObject.value = ".\lib"

$contentRootPathObject = $brierleyFrameworkWebApiConfigFileObject.configuration.appSettings.add | where {$_.key -eq 'ContentRootPath'}
$contentRootPathObject.value = "C:\inetpub\wwwroot\ContentRoot"

$brierleyFrameworkWebApiConfigFileObject.Save($brierleyFrameworkWebApiConfigFilePath)
Write-Output "$(Get-Date -format T) - Brierley Framework WebApi Configuration File Updated! Loyalty Ware Configuration Set!"


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
