<#
.SYNOPSIS
  Instaluje lokalny silnik Maszyny Głosów na Windows i przygotowuje wpis dla aplikacji Claude.

.DESCRIPTION
  1. znajduje Pythona 3.10-3.12 (launcher "py"),
  2. tworzy środowisko .venv w folderze voice-machine,
  3. instaluje PyTorch (adres indeksu podajesz w -TorchIndexUrl albo wybierasz -CpuOnly),
  4. sprawdza, czy PyTorch widzi kartę NVIDIA (gdy nie wybrałeś -CpuOnly),
  5. instaluje silnik: pip install -e ".[<silnik>]",
  6. uruchamia "doctor --load": pobiera model, robi próbną syntezę oraz próbę klonowania,
  7. zapisuje claude-desktop-snippet.json z prawdziwymi ścieżkami
     (z -InstallToClaudeConfig dopisuje wpis do konfiguracji Claude, po zrobieniu kopii zapasowej).

  Dane (głosy znajomych i nagrania) trafiają do %USERPROFILE%\SakuraVoiceMachine. Ta ścieżka jest wpisywana do konfiguracji
  jako SVM_DATA_DIR, żeby leżała poza AppData (łatwo ją znaleźć, a wersja aplikacji Claude ze sklepu Microsoft jej nie przekierowuje).

  UWAGA: ten skrypt nie był uruchamiany w środowisku, w którym powstał (brak PowerShella).
  Jest krótki i każdy krok wypisuje, co robi, więc błąd będzie widać od razu.

.PARAMETER TorchIndexUrl
  Adres indeksu PyTorch z polecenia wygenerowanego na https://pytorch.org/get-started/locally/
  (Windows, Pip, Python, wersja CUDA pasująca do Twojej karty): wartość po --index-url.
  Nie zgaduję jej, bo zależy od karty i sterownika.

.PARAMETER CpuOnly
  Instaluje PyTorch w wersji CPU z PyPI. Działa, ale synteza jest wielokrotnie wolniejsza.

.PARAMETER ConfigOnly
  Nie instaluje niczego: tylko zapisuje claude-desktop-snippet.json i (z -InstallToClaudeConfig) wpis w konfiguracji Claude.
  Wymaga gotowego środowiska .venv z wcześniejszej instalacji.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -TorchIndexUrl https://download.pytorch.org/whl/cuXXX
  (podstaw adres z pytorch.org, "cuXXX" to tylko miejsce na Twoją wersję CUDA)
  Przełącznik -ExecutionPolicy Bypass jest potrzebny, bo świeży Windows domyślnie (polityka Restricted) nie uruchamia skryptów .ps1;
  działa tylko dla tego jednego uruchomienia i niczego w systemie nie zmienia.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -ConfigOnly -InstallToClaudeConfig
  (po udanej instalacji: dopisuje serwer do konfiguracji aplikacji Claude, z kopią zapasową)
#>
[CmdletBinding()]
param(
    [string]$Engine = "voxcpm",
    [string]$TorchIndexUrl = "",
    [switch]$CpuOnly,
    [switch]$ConfigOnly,
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

function Find-ClaudeConfig {
    # Wersja aplikacji Claude ze sklepu Microsoft (MSIX) trzyma konfigurację w katalogu pakietu, zwykła instalacja w %APPDATA%.
    $packages = Join-Path $env:LOCALAPPDATA "Packages"
    if (Test-Path -LiteralPath $packages) {
        $dirs = Get-ChildItem -LiteralPath $packages -Directory -Filter "Claude_*" -ErrorAction SilentlyContinue
        foreach ($dir in $dirs) {
            $file = Join-Path $dir.FullName "LocalCache\Roaming\Claude\claude_desktop_config.json"
            if (Test-Path -LiteralPath $file) { return $file }
        }
    }
    return (Join-Path $env:APPDATA "Claude\claude_desktop_config.json")
}

if (-not $ConfigOnly -and -not $TorchIndexUrl -and -not $CpuOnly) {
    Write-Host @"

Najpierw wybierz wersję PyTorch, bo od niej zależy, czy model pojedzie na karcie graficznej:

  1. Wejdź na https://pytorch.org/get-started/locally/ i wybierz: Stable, Windows, Pip, Python, wersję CUDA dla swojej karty NVIDIA.
  2. Z wygenerowanego polecenia weź adres po --index-url i uruchom skrypt ponownie:
       powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -TorchIndexUrl <ten adres>
  3. Bez karty NVIDIA użyj -CpuOnly (działa, ale jest wolno).

Niczego jeszcze nie zainstalowano.
"@ -ForegroundColor Yellow
    exit 2
}

$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$dataDir = Join-Path $env:USERPROFILE "SakuraVoiceMachine"

if ($ConfigOnly) {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Nie ma środowiska .venv w tym folderze. Najpierw wykonaj pełną instalację (bez -ConfigOnly)."
    }
} else {
    Write-Step "Szukam Pythona 3.10-3.12"
    $python = Find-Python
    if (-not $python) {
        throw "Nie znaleziono Pythona 3.10, 3.11 ani 3.12 (launcher 'py'). Zainstaluj Pythona 3.11 z python.org (model nie działa jeszcze na 3.13) i uruchom skrypt ponownie."
    }
    Write-Host "Python: $python"

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

    if (-not $CpuOnly) {
        Write-Step "Sprawdzam, czy PyTorch widzi kartę NVIDIA"
        & $venvPython -c "import sys, torch; sys.exit(0 if torch.cuda.is_available() else 3)"
        if ($LASTEXITCODE -eq 3) {
            throw "PyTorch nie widzi karty NVIDIA (CUDA). Najczęstsze przyczyny: adres indeksu nie pasuje do Twojej karty albo sterownika (sprawdź polecenie nvidia-smi i stronę pytorch.org/get-started/locally), albo karta nie jest NVIDIA. Bez karty uruchom skrypt z -CpuOnly."
        }
        if ($LASTEXITCODE -ne 0) {
            throw "PyTorch nie daje się wczytać (kod wyjścia $LASTEXITCODE, szczegóły powyżej). Na świeżym Windows najczęściej brakuje 'Visual C++ Redistributable x64': https://aka.ms/vs/17/release/vc_redist.x64.exe"
        }
        Write-Host "PyTorch widzi kartę NVIDIA." -ForegroundColor Green
    }

    Write-Step "Instaluję silnik '$Engine' (pierwsza instalacja trwa kilka minut)"
    Invoke-Checked "instalacja silnika" { & $venvPython -m pip install -e ".[$Engine]" }

    if (-not $SkipDoctor) {
        Write-Step "Sprawdzam środowisko i robię próbną syntezę oraz próbę klonowania (pierwszy raz pobiera model, może to potrwać)"
        & $venvPython -m voice_machine doctor --engine $Engine --data-dir $dataDir --load
        if ($LASTEXITCODE -ne 0) {
            throw "doctor wykrył problem (patrz wyżej). Nie dodawaj serwera do Claude, dopóki doctor nie przejdzie."
        }
        Write-Host "Posłuchaj plików doctor-smoke.wav (głos modelu) i doctor-smoke-clone.wav (ten sam głos po klonowaniu) w tym folderze: tylko tak ocenisz, czy głos brzmi sensownie." -ForegroundColor Green
    }
}

Write-Step "Przygotowuję wpis dla aplikacji Claude"
# Aplikacja Claude uruchamia serwer z krótką listą zmiennych środowiskowych, więc to, co ustawiłeś w swojej powłoce
# (pamięć podręczna Hugging Face, serwer proxy), trzeba przekazać jawnie w bloku "env".
$serverEnv = [ordered]@{ SVM_ENGINE = $Engine; SVM_DATA_DIR = $dataDir }
if ($CpuOnly) { $serverEnv["SVM_DEVICE"] = "cpu" }
foreach ($name in @("HF_HOME", "HF_HUB_CACHE", "HF_ENDPOINT", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ($value) { $serverEnv[$name] = $value }
}
$entry = [ordered]@{
    command = $venvPython
    args    = @("-m", "voice_machine")
    env     = $serverEnv
}
$snippet = [ordered]@{ mcpServers = [ordered]@{ "sakura-voice" = $entry } }
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$snippetPath = Join-Path $root "claude-desktop-snippet.json"
[System.IO.File]::WriteAllText($snippetPath, ($snippet | ConvertTo-Json -Depth 10), $utf8NoBom)
Write-Host "Zapisano: $snippetPath"

if ($InstallToClaudeConfig) {
    $configPath = Find-ClaudeConfig
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
    # Istniejący wpis "sakura-voice" zachowuje własne zmienne env (np. SVM_DATA_DIR, SVM_MAX_OUTPUTS); nadpisujemy tylko SVM_ENGINE,
    # a pozostałe nasze zmienne dopisujemy, gdy ich jeszcze nie ma.
    $mergedEnv = [ordered]@{}
    $existing = $config.mcpServers.PSObject.Properties["sakura-voice"]
    $replacing = $false
    if ($existing) {
        $replacing = $true
        if ($existing.Value.PSObject.Properties["env"]) {
            foreach ($property in $existing.Value.env.PSObject.Properties) { $mergedEnv[$property.Name] = $property.Value }
        }
    }
    foreach ($key in $serverEnv.Keys) {
        if ($key -eq "SVM_ENGINE" -or -not $mergedEnv.Contains($key)) { $mergedEnv[$key] = $serverEnv[$key] }
    }
    $configEntry = [ordered]@{
        command = $venvPython
        args    = @("-m", "voice_machine")
        env     = $mergedEnv
    }
    $config.mcpServers | Add-Member -NotePropertyName "sakura-voice" -NotePropertyValue ([pscustomobject]$configEntry) -Force
    [System.IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 20), $utf8NoBom)
    if ($replacing) {
        Write-Host "Zaktualizowano istniejący wpis 'sakura-voice' (zachowano Twoje zmienne env) w: $configPath" -ForegroundColor Green
    } else {
        Write-Host "Dopisano 'sakura-voice' do: $configPath" -ForegroundColor Green
    }
    Write-Host "Sprawdź w aplikacji Claude (Ustawienia, Developer, Edit Config), że to ten plik: jeśli aplikacja pokazuje inną ścieżkę, wklej wpis ręcznie." -ForegroundColor Yellow
} else {
    Write-Host @"

Ostatni krok: dodaj serwer do aplikacji Claude.
  Najprościej: uruchom skrypt jeszcze raz z -ConfigOnly -InstallToClaudeConfig, a dopisze wpis sam (z kopią zapasową pliku konfiguracji).
  Ręcznie: w aplikacji Claude (komputerowej) otwórz Ustawienia, Developer, Edit Config.
    - Jeśli plik nie ma klucza "mcpServers", dopisz cały zapis z claude-desktop-snippet.json obok innych kluczy.
    - Jeśli już ma, skopiuj do niego tylko wpis "sakura-voice": { ... } (nazwa musi zostać "sakura-voice").
"@
}

Write-Host "`nGotowe. Zamknij aplikację Claude całkiem (także z zasobnika), uruchom ją ponownie i otwórz artefakt Maszyna Głosów w niej." -ForegroundColor Green
