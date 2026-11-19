<#
.SYNOPSIS
  Instaluje lokalny silnik Maszyny Głosów na Windows i przygotowuje wpis dla aplikacji Claude.

.DESCRIPTION
  1. znajduje Pythona 3.10-3.12 (launcher "py"),
  2. tworzy środowisko .venv w folderze voice-machine,
  3. instaluje PyTorch (adres indeksu podajesz w -TorchIndexUrl albo wybierasz -CpuOnly),
  4. instaluje silnik: pip install -e ".[<silnik>]",
  5. uruchamia "doctor --load": pobiera model i robi próbną syntezę,
  6. zapisuje claude-desktop-snippet.json z prawdziwymi ścieżkami
     (z -InstallToClaudeConfig dopisuje wpis do konfiguracji Claude, po zrobieniu kopii zapasowej).

  UWAGA: ten skrypt nie był uruchamiany w środowisku, w którym powstał (brak PowerShella).
  Jest krótki i każdy krok wypisuje, co robi, więc błąd będzie widać od razu.

.PARAMETER TorchIndexUrl
  Adres indeksu PyTorch z polecenia wygenerowanego na https://pytorch.org/get-started/locally/
  (Windows, Pip, Python, wersja CUDA pasująca do Twojej karty): wartość po --index-url.
  Nie zgaduję jej, bo zależy od karty i sterownika.

.PARAMETER CpuOnly
  Instaluje PyTorch w wersji CPU z PyPI. Działa, ale synteza jest wielokrotnie wolniejsza.

.EXAMPLE
  .\scripts\setup-windows.ps1 -TorchIndexUrl https://download.pytorch.org/whl/cuXXX
  (podstaw adres z pytorch.org, "cuXXX" to tylko miejsce na Twoją wersję CUDA)
#>
[CmdletBinding()]
param(
    [string]$Engine = "voxcpm",
    [string]$TorchIndexUrl = "",
    [switch]$CpuOnly,
    [switch]$SkipDoctor,
    [switch]$InstallToClaudeConfig
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

function Write-Step([string]$Text) { Write-Host "`n==> $Text" -ForegroundColor Magenta }

function Invoke-Checked([string]$What, [scriptblock]$Block) {
    & $Block
    if ($LASTEXITCODE -ne 0) { throw "Nie powiodło się: $What (kod wyjścia $LASTEXITCODE)." }
}

function Find-Python {
    # Kolejność: 3.11 (zalecana), potem 3.10, na końcu 3.12. 3.13 i nowsze są pomijane (model ich nie wspiera).
    foreach ($version in @("3.11", "3.10", "3.12")) {
        try {
            $exe = & py "-$version" -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) { return ($exe | Select-Object -First 1).Trim() }
        } catch { }
    }
    return $null
}

if (-not $TorchIndexUrl -and -not $CpuOnly) {
    Write-Host @"

Najpierw wybierz wersję PyTorch, bo od niej zależy, czy model pojedzie na karcie graficznej:

  1. Wejdź na https://pytorch.org/get-started/locally/ i wybierz: Stable, Windows, Pip, Python, wersję CUDA dla swojej karty NVIDIA.
  2. Z wygenerowanego polecenia weź adres po --index-url i uruchom skrypt ponownie:
       .\scripts\setup-windows.ps1 -TorchIndexUrl <ten adres>
  3. Bez karty NVIDIA użyj -CpuOnly (działa, ale jest wolno).

Niczego jeszcze nie zainstalowano.
"@ -ForegroundColor Yellow
    exit 2
}

Write-Step "Szukam Pythona 3.10-3.12"
$python = Find-Python
if (-not $python) {
    throw "Nie znaleziono Pythona 3.10, 3.11 ani 3.12 (launcher 'py'). Zainstaluj Pythona 3.11 z python.org (model nie działa jeszcze na 3.13) i uruchom skrypt ponownie."
}
Write-Host "Python: $python"

$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Step "Tworzę środowisko .venv"
    Invoke-Checked "tworzenie środowiska" { & $python -m venv $venvDir }
} else {
    Write-Host "Środowisko .venv już istnieje, używam go."
}

Write-Step "Aktualizuję pip"
Invoke-Checked "aktualizacja pip" { & $venvPython -m pip install --upgrade pip }

Write-Step "Instaluję PyTorch"
if ($TorchIndexUrl) {
    Invoke-Checked "PyTorch" { & $venvPython -m pip install torch torchaudio --index-url $TorchIndexUrl }
} else {
    Invoke-Checked "PyTorch (CPU)" { & $venvPython -m pip install torch torchaudio }
}

Write-Step "Instaluję silnik '$Engine' (pierwsza instalacja trwa kilka minut)"
Invoke-Checked "instalacja silnika" { & $venvPython -m pip install -e ".[$Engine]" }

if (-not $SkipDoctor) {
    Write-Step "Sprawdzam środowisko i robię próbną syntezę (pierwszy raz pobiera model, może to potrwać)"
    & $venvPython -m voice_machine doctor --engine $Engine --load
    if ($LASTEXITCODE -ne 0) {
        throw "doctor wykrył problem (patrz wyżej). Nie dodawaj serwera do Claude, dopóki doctor nie przejdzie."
    }
    Write-Host "Posłuchaj pliku doctor-smoke.wav w tym folderze: tylko tak ocenisz, czy głos brzmi sensownie." -ForegroundColor Green
}

Write-Step "Przygotowuję wpis dla aplikacji Claude"
$entry = [ordered]@{
    command = $venvPython
    args    = @("-m", "voice_machine")
    env     = [ordered]@{ SVM_ENGINE = $Engine }
}
$snippet = [ordered]@{ mcpServers = [ordered]@{ "sakura-voice" = $entry } }
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$snippetPath = Join-Path $root "claude-desktop-snippet.json"
[System.IO.File]::WriteAllText($snippetPath, ($snippet | ConvertTo-Json -Depth 10), $utf8NoBom)
Write-Host "Zapisano: $snippetPath"

if ($InstallToClaudeConfig) {
    $configPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
    if (Test-Path -LiteralPath $configPath) {
        $backup = "$configPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
        Copy-Item -LiteralPath $configPath -Destination $backup
        Write-Host "Kopia zapasowa konfiguracji: $backup"
        $raw = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8
        $config = if ($raw -and $raw.Trim()) { $raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $configPath) | Out-Null
        $config = [pscustomobject]@{}
    }
    if (-not $config.PSObject.Properties["mcpServers"]) {
        $config | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{})
    }
    $config.mcpServers | Add-Member -NotePropertyName "sakura-voice" -NotePropertyValue ([pscustomobject]$entry) -Force
    [System.IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 20), $utf8NoBom)
    Write-Host "Dopisano 'sakura-voice' do: $configPath" -ForegroundColor Green
} else {
    Write-Host @"

Ostatni krok ręczny: w aplikacji Claude (komputerowej) otwórz Ustawienia, Developer, Edit Config
i wklej zawartość pliku claude-desktop-snippet.json do sekcji "mcpServers" (nazwa musi zostać "sakura-voice").
Albo uruchom ten skrypt jeszcze raz z -InstallToClaudeConfig, a dopisze wpis sam (z kopią zapasową).
"@
}

Write-Host "`nGotowe. Zamknij aplikację Claude całkiem (także z zasobnika), uruchom ją ponownie i otwórz artefakt Maszyna Głosów w niej." -ForegroundColor Green
