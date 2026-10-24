param([string]$EngineRoot='C:\Program Files\Epic Games\UE_5.8')
$ErrorActionPreference='Stop'
$editorExe=Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$project=Join-Path $PSScriptRoot 'Unreal\XiuXianTown\XiuXianTown.uproject'
if (-not (Test-Path -LiteralPath $editorExe)) { throw "找不到 Unreal Editor，請指定 -EngineRoot。" }
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Unreal\XiuXianTown\Binaries\Win64\UnrealEditor-XiuXianTown.dll'))) { throw '請先用 Unreal Editor 編譯 XiuXianTown 模組。' }
# User-run launcher opens the interactive game window. This is not a packaged executable.
& $editorExe $project '/Game/Maps/TownLayout_13' -game -windowed -ResX=1600 -ResY=900 -NoLiveCoding
