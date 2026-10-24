param(
    [ValidateSet('BuildMap','Test','Capture')][string]$Task = 'Test',
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [string]$ResumeSlot = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$projectFile = Join-Path $projectRoot 'XiuXianTown\XiuXianTown.uproject'
$scriptNames = @{BuildMap='build_management10.py';Test='test_management10.py';Capture='capture_management10.py'}
$scriptFile = Join-Path $PSScriptRoot $scriptNames[$Task]
$editorExe = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $editorExe)) { throw "Unreal Editor not found: $editorExe" }
if (-not (Test-Path -LiteralPath $scriptFile)) { throw "Script not found: $scriptFile" }
$runLog = Join-Path $projectRoot ('management10_'+$Task.ToLower()+'.log')
$testSlot = 'Management10_Test_'+(Get-Date -Format 'yyyyMMdd_HHmmss')
if ($ResumeSlot) { $testSlot=$ResumeSlot }
$editorArgs = @(('"'+$projectFile+'"'),('-ExecutePythonScript="'+$scriptFile+'"'),'-unattended','-RenderOffscreen','-nosound','-nosplash','-NoLiveCoding',('-abslog="'+$runLog+'"'),('-SectSaveSlot='+$testSlot))
if ($ResumeSlot) {
    if ($ResumeSlot -notmatch '^Management10_Test_[0-9_]+$') { throw 'ResumeSlot must be an isolated management test checkpoint.' }
    $editorArgs += '-SectResumeSlot='+$ResumeSlot
}
Start-Process -FilePath $editorExe -ArgumentList $editorArgs -WindowStyle Hidden -PassThru | Select-Object Id
