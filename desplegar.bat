@echo off
echo ========================================
echo   Sistema de Gestion Documental
echo   Instalacion Automatica para Windows
echo ========================================
echo.

REM Verificar si Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker no esta instalado.
    echo Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Verificar si Docker Compose está disponible
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose no esta disponible.
    echo Asegurate de que Docker Desktop este corriendo.
    pause
    exit /b 1
)

echo [INFO] Docker encontrado correctamente.
echo.

REM Crear directorios necesarios
echo [INFO] Creando directorios necesarios...
if not exist "static\uploads" mkdir static\uploads
if not exist "logs" mkdir logs
if not exist "instance" mkdir instance

REM Crear archivo .env si no existe
if not exist ".env" (
    echo [INFO] Creando archivo de configuracion...
    copy env.example .env >nul
    echo [INFO] Archivo .env creado. Puedes editarlo si necesitas cambiar configuraciones.
    echo [INFO] Usando SQLite - No se requiere configuracion de base de datos.
)

echo.
echo [INFO] Construyendo imagen Docker...
docker-compose build --no-cache

if %errorlevel% neq 0 (
    echo [ERROR] Error al construir la imagen Docker.
    pause
    exit /b 1
)

echo.
echo [INFO] Parando contenedores existentes...
docker-compose down >nul 2>&1

echo [INFO] Iniciando servicios...
docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Error al iniciar los servicios.
    pause
    exit /b 1
)

echo.
echo [INFO] Esperando a que los servicios esten listos...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo   ¡INSTALACION COMPLETADA!
echo ========================================
echo.
echo [ACCESO]
echo URL: http://localhost:8080
echo Admin: admin / admin123
echo Area: jefe_sanidad / sanidad123
echo.
echo [COMANDOS UTILES]
echo Ver logs: docker-compose logs -f
echo Parar: docker-compose down
echo Reiniciar: docker-compose restart
echo.
echo [INFO] Los archivos se guardan en: static\uploads
echo [INFO] Los logs se guardan en: logs\
echo.
echo ========================================
pause
