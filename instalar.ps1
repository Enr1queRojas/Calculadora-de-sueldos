Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appName   = "Calculadora de Nomina Innoverse"

function Show-Message($texto, $titulo, $botones, $icono) {
    return [System.Windows.Forms.MessageBox]::Show(
        $texto, $titulo, $botones, $icono
    )
}

# ── Paso 1: Bienvenida ────────────────────────────────────────────────────────
$r = Show-Message `
    "Bienvenido al instalador de`n$appName`n`nEste asistente configurara todo lo necesario para ejecutar la aplicacion.`n`nPresiona Si para continuar." `
    "Instalador" `
    ([System.Windows.Forms.MessageBoxButtons]::YesNo) `
    ([System.Windows.Forms.MessageBoxIcon]::Information)

if ($r -eq [System.Windows.Forms.DialogResult]::No) { exit }

# ── Paso 2: Verificar Python ──────────────────────────────────────────────────
$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") { $pythonCmd = $cmd; break }
    } catch {}
}

if (-not $pythonCmd) {
    Show-Message `
        "Python no esta instalado en este equipo.`n`nSe abrira la pagina oficial de descarga.`n`nInstrucciones:`n  1. Descarga Python 3 (boton amarillo grande)`n  2. En el instalador, ACTIVA la casilla 'Add Python to PATH'`n  3. Completa la instalacion`n  4. Vuelve a ejecutar este instalador" `
        "Python no encontrado" `
        ([System.Windows.Forms.MessageBoxButtons]::OK) `
        ([System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null

    Start-Process "https://www.python.org/downloads/"
    exit
}

$verActual = & $pythonCmd --version 2>&1
Show-Message `
    "Python encontrado: $verActual`n`nAhora se instalaran las dependencias.`nEsto puede tardar 1-2 minutos..." `
    "Verificacion exitosa" `
    ([System.Windows.Forms.MessageBoxButtons]::OK) `
    ([System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null

# ── Paso 3: Crear entorno virtual e instalar dependencias ─────────────────────
Set-Location $scriptDir

$venvPath    = Join-Path $scriptDir ".venv"
$pipExe      = Join-Path $venvPath "Scripts\pip.exe"
$streamlitExe = Join-Path $venvPath "Scripts\streamlit.exe"

if (-not (Test-Path $venvPath)) {
    & $pythonCmd -m venv .venv | Out-Null
}

# Actualizar pip silenciosamente
& $pipExe install --upgrade pip --quiet 2>&1 | Out-Null

# Instalar dependencias
$reqFile = Join-Path $scriptDir "requirements.txt"
$installOutput = & $pipExe install -r $reqFile --quiet 2>&1

if ($LASTEXITCODE -ne 0) {
    Show-Message `
        "Hubo un error al instalar las dependencias:`n`n$installOutput`n`nRevisa tu conexion a internet e intenta de nuevo." `
        "Error de instalacion" `
        ([System.Windows.Forms.MessageBoxButtons]::OK) `
        ([System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    exit 1
}

# ── Paso 4: Crear iniciar.bat con el entorno virtual ─────────────────────────
$launchContent = "@echo off`r`ncd /d `"$scriptDir`"`r`n`"$streamlitExe`" run app.py`r`n"
Set-Content -Path (Join-Path $scriptDir "iniciar.bat") -Value $launchContent -Encoding ASCII

# ── Paso 5: Crear acceso directo en el Escritorio ────────────────────────────
$desktopPath  = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "$appName.lnk"
$launchBat    = Join-Path $scriptDir "iniciar.bat"

$shell    = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath       = $launchBat
$shortcut.WorkingDirectory = $scriptDir
$shortcut.IconLocation     = "shell32.dll,21"
$shortcut.Description      = $appName
$shortcut.Save()

# ── Paso 6: Finalizar ─────────────────────────────────────────────────────────
$r = Show-Message `
    "Instalacion completada con exito.`n`nSe creo un acceso directo en tu Escritorio llamado:`n'$appName'`n`nDeseas abrir la aplicacion ahora?" `
    "Listo" `
    ([System.Windows.Forms.MessageBoxButtons]::YesNo) `
    ([System.Windows.Forms.MessageBoxIcon]::Information)

if ($r -eq [System.Windows.Forms.DialogResult]::Yes) {
    Start-Process $launchBat
}
