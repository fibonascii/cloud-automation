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
$bootstrapRepository = (Get-SSMParameterValue -Names $ClientCode-bootstrapRepository -WithDecryption $true).Parameters[0].Value
$loyaltyWareOrganization = (Get-SSMParameterValue -Names $ClientCode-loyaltyWareOrganization -WithDecryption $true).Parameters[0].Value
Write-Host "LoyaltyWare Organization =" $loyaltyWareOrganization 
$loyaltyWareEnvironment = (Get-SSMParameterValue -Names $ClientCode-loyaltyWareEnvironment -WithDecryption $true).Parameters[0].Value
Write-Host "LoyaltyWare Environment =" $loyaltyWareEnvironment
Write-Output "$(Get-Date -format T) - Retrieved Input Parameters!"
$region = 'us-east-1'
$keyPrefix = 'bootstrap/rest/files/'

$localPath = 'C:/bootstrap/rest/files'

Write-Output "$(Get-Date -format T) - Downloading Files from S3"
if (-Not (Test-Path -Path $localPath)){New-Item -Path $localPath -ItemType directory -Force | out-null}
$artifacts = Get-S3Object -BucketName $bootstrapRepository -KeyPrefix $keyPrefix -Region $region
foreach($artifact in $artifacts) {$localFileName = $artifact.Key -replace $keyPrefix, '' 
if ($localFileName -ne '') {$localFilePath = Join-Path $localPath $localFileName 
Copy-S3Object -BucketName $bootstrapRepository -Key $artifact.Key -LocalFile $localFilePath -Region $region}} 

Write-Output "$(Get-Date -format T) - Files successfully Downloaded from S3!"


$loyaltyConfigurationDir = ("C:\inetpub\wwwroot\LWConfig\" + $loyaltyWareOrganization + "_" + $loyaltyWareEnvironment)
if(!(Test-Path -Path $loyaltyConfigurationDir )){
    New-Item -ItemType directory -Path $loyaltyConfigurationDir
}

Write-Output "$(Get-Date -format T) - Moving new DBConfig file to folder."
Move-Item -Path "C:\bootstrap\rest\files\DBConfig.dat" -Destination $loyaltyConfigurationDir -Force
Move-Item -Path "C:\bootstrap\rest\files\Keystore.dat" -Destination $loyaltyConfigurationDir -Force
Move-Item -Path "C:\bootstrap\rest\files\SymmetricKeystore.dat" -Destination $loyaltyConfigurationDir -Force
Move-Item -Path "C:\bootstrap\rest\files\Framework.cfg" -Destination $loyaltyConfigurationDir -Force

Write-Output "$(Get-Date -format T) - Successfully moved DBConfig file to folder."


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
