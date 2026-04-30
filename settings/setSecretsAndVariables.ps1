# ---------------------------------------------
# Entorno DEV
# ---------------------------------------------
$env = "development"
# Secretos 
$fileSecrets = ".\repo-secrets-dev.env"
gh secret set --env $env -f $fileSecrets

# Variables
$fileVariables = ".\repo-variables-dev.env"
gh variable set --env $env -f $fileVariables

# Credentials yml publish profile app-dev-api
$filePublishProfile = ".\repo-publishprofile-dev-001.yml"
$secretName = "PUBLISHPROFILE_DEV_001"
$publishProfileContent = Get-Content $filePublishProfile -Raw
$publishProfileContent | gh secret set $secretName --env $env
