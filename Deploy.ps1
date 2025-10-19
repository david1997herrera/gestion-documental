# Sistema de Gestión Documental - Despliegue en Windows
# PowerShell Script

param(
    [switch]$Force,
    [switch]$SkipPortCheck,
    [string]$Port = "8080"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Sistema de Gestión Documental" -ForegroundColor Cyan
Write-Host "   Despliegue en Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Función para verificar comandos
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Verificar Docker
Write-Host "[1/5] Verificando Docker..." -ForegroundColor Yellow
if (-not (Test-Command "docker")) {
    Write-Host "ERROR: Docker no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "✓ Docker encontrado" -ForegroundColor Green

if (-not (Test-Command "docker-compose")) {
    Write-Host "ERROR: Docker Compose no encontrado" -ForegroundColor Red
    Write-Host "Por favor instala Docker Desktop completo" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "✓ Docker Compose encontrado" -ForegroundColor Green
Write-Host ""

# Verificar puerto
if (-not $SkipPortCheck) {
    Write-Host "[2/5] Verificando puerto $Port..." -ForegroundColor Yellow
    $portCheck = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($portCheck) {
        Write-Host "ADVERTENCIA: Puerto $Port está en uso" -ForegroundColor Yellow
        Write-Host "La aplicación usará el puerto $Port cuando se inicie" -ForegroundColor Yellow
        Write-Host "Si hay conflictos, edita docker-compose.yml" -ForegroundColor Yellow
        if (-not $Force) {
            $continue = Read-Host "¿Continuar? (s/N)"
            if ($continue -ne "s" -and $continue -ne "S") {
                Write-Host "Despliegue cancelado" -ForegroundColor Red
                exit 0
            }
        }
        Write-Host ""
    }
    Write-Host "✓ Puerto verificado" -ForegroundColor Green
    Write-Host ""
}

# Detener contenedores existentes
Write-Host "[3/5] Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down
Write-Host "✓ Contenedores detenidos" -ForegroundColor Green
Write-Host ""

# Construir aplicación
Write-Host "[4/5] Construyendo aplicación..." -ForegroundColor Yellow
Write-Host "Esto puede tomar unos minutos en la primera ejecución..." -ForegroundColor Gray
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló al construir la aplicación" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "✓ Aplicación construida" -ForegroundColor Green
Write-Host ""

# Desplegar aplicación
Write-Host "[5/5] Desplegando aplicación..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Falló al desplegar la aplicación" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "✓ Aplicación desplegada" -ForegroundColor Green
Write-Host ""

# Verificar estado
Write-Host "Verificando estado..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
docker-compose ps
Write-Host ""

# Mostrar información
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DESPLIEGUE COMPLETADO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "La aplicación está disponible en:" -ForegroundColor White
Write-Host "  http://localhost:$Port" -ForegroundColor Green
Write-Host ""
Write-Host "Credenciales de acceso:" -ForegroundColor White
Write-Host "  Usuario: admin" -ForegroundColor Yellow
Write-Host "  Password: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor White
Write-Host "  Ver logs:     docker-compose logs web" -ForegroundColor Gray
Write-Host "  Reiniciar:    docker-compose restart" -ForegroundColor Gray
Write-Host "  Detener:      docker-compose down" -ForegroundColor Gray
Write-Host "  Actualizar:   git pull && docker-compose build && docker-compose up -d" -ForegroundColor Gray
Write-Host ""

# Abrir navegador
$openBrowser = Read-Host "¿Abrir navegador automáticamente? (S/n)"
if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
    Write-Host "Abriendo navegador..." -ForegroundColor Yellow
    Start-Process "http://localhost:$Port"
    Write-Host "¡Listo! La aplicación debería abrirse en tu navegador." -ForegroundColor Green
    Write-Host "Si no se abre automáticamente, ve a: http://localhost:$Port" -ForegroundColor Gray
}

Write-Host ""
Read-Host "Presiona Enter para salir"
