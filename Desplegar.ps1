# Script de despliegue PowerShell para Sistema de Gestión Documental
# Ejecutar como: PowerShell -ExecutionPolicy Bypass -File Desplegar.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sistema de Gestion Documental" -ForegroundColor Cyan
Write-Host "  Instalacion Automatica para Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Función para imprimir mensajes con colores
function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    switch ($Type) {
        "INFO" { Write-Host "[INFO] $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "[ERROR] $Message" -ForegroundColor Red }
        "SUCCESS" { Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
    }
}

# Verificar si Docker está instalado
Write-Status "Verificando Docker..."
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker encontrado: $dockerVersion" "SUCCESS"
    } else {
        throw "Docker no está instalado"
    }
} catch {
    Write-Status "Docker no está instalado. Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop" "ERROR"
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar si Docker está corriendo
Write-Status "Verificando que Docker esté corriendo..."
try {
    docker ps >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no está corriendo"
    }
    Write-Status "Docker está corriendo correctamente" "SUCCESS"
} catch {
    Write-Status "Docker no está corriendo. Por favor inicia Docker Desktop" "ERROR"
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar Docker Compose
Write-Status "Verificando Docker Compose..."
try {
    $composeVersion = docker-compose --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker Compose encontrado: $composeVersion" "SUCCESS"
    } else {
        throw "Docker Compose no está disponible"
    }
} catch {
    Write-Status "Docker Compose no está disponible. Asegúrate de que Docker Desktop esté actualizado" "ERROR"
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Crear directorios necesarios
Write-Status "Creando directorios necesarios..."
$directories = @("static\uploads", "logs", "instance")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Status "Directorio creado: $dir"
    }
}

# Crear archivo .env si no existe
if (!(Test-Path ".env")) {
    Write-Status "Creando archivo de configuración..."
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Status "Archivo .env creado desde env.example"
    } else {
        Write-Status "Creando archivo .env básico..."
        @"
# Configuración de la Base de Datos
DATABASE_URL=postgresql://admin:admin123@db:5432/gestion_documental

# Configuración de Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
EMAIL_SENDER=estadisticatessa@gmail.com
EMAIL_PASSWORD=rxcd epqr gebp myhj

# Configuración de Seguridad
SECRET_KEY=gestion_documental_secret_key_2024_very_secure

# Configuración del Servidor
FLASK_ENV=production
HOST=0.0.0.0
PORT=8080

# Configuración de Archivos
UPLOAD_FOLDER=static/uploads
MAX_FILE_SIZE=16777216
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Status "Archivo .env creado con configuración básica"
    }
}

# Construir imagen Docker
Write-Status "Construyendo imagen Docker..."
Write-Host "Esto puede tomar varios minutos..." -ForegroundColor Yellow
docker-compose build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Status "Error al construir la imagen Docker" "ERROR"
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Status "Imagen construida correctamente" "SUCCESS"

# Parar contenedores existentes
Write-Status "Parando contenedores existentes..."
docker-compose down 2>$null | Out-Null

# Iniciar servicios
Write-Status "Iniciando servicios..."
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Status "Error al iniciar los servicios" "ERROR"
    Write-Status "Mostrando logs para diagnóstico..."
    docker-compose logs
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Esperar a que los servicios estén listos
Write-Status "Esperando a que los servicios estén listos..."
Write-Host "Esto puede tomar hasta 2 minutos..." -ForegroundColor Yellow

$timeout = 120 # 2 minutos
$elapsed = 0
$interval = 10

while ($elapsed -lt $timeout) {
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -UseBasicParsing 2>$null
        if ($response.StatusCode -eq 200) {
            Write-Status "Servicios iniciados correctamente" "SUCCESS"
            break
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
    
    if ($elapsed -ge $timeout) {
        Write-Status "Timeout esperando servicios. Verificando estado..." "WARNING"
        docker-compose ps
        break
    }
}

# Mostrar información final
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ¡INSTALACIÓN COMPLETADA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[ACCESO]" -ForegroundColor Cyan
Write-Host "URL: http://localhost:8080" -ForegroundColor White
Write-Host "Admin: admin / admin123" -ForegroundColor White
Write-Host "Área: jefe_sanidad / sanidad123" -ForegroundColor White
Write-Host ""
Write-Host "[COMANDOS ÚTILES]" -ForegroundColor Cyan
Write-Host "Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "Parar: docker-compose down" -ForegroundColor White
Write-Host "Reiniciar: docker-compose restart" -ForegroundColor White
Write-Host "Estado: docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "[ARCHIVOS]" -ForegroundColor Cyan
Write-Host "Uploads: static\uploads\" -ForegroundColor White
Write-Host "Logs: logs\" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Green

# Abrir navegador
$openBrowser = Read-Host "¿Abrir navegador ahora? (s/n)"
if ($openBrowser -eq "s" -or $openBrowser -eq "S" -or $openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:8080"
}

Read-Host "Presiona Enter para salir"
