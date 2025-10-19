@echo off
echo ========================================
echo   Sistema de Gestion Documental
echo   Despliegue en Windows
echo ========================================
echo.

echo [1/4] Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta instalado o no esta en el PATH
    echo Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✓ Docker encontrado

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose no encontrado
    echo Por favor instala Docker Desktop completo
    pause
    exit /b 1
)
echo ✓ Docker Compose encontrado
echo.

echo [2/4] Verificando puerto 8080...
netstat -an | findstr :8080 >nul 2>&1
if %errorlevel% equ 0 (
    echo ADVERTENCIA: Puerto 8080 esta en uso
    echo La aplicacion usara el puerto 8080 cuando se inicie
    echo Si hay conflictos, edita docker-compose.yml
    echo.
)
echo ✓ Puerto verificado
echo.

echo [3/4] Construyendo y desplegando aplicacion...
echo Esto puede tomar unos minutos en la primera ejecucion...
docker-compose down
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo ERROR: Fallo al construir la aplicacion
    pause
    exit /b 1
)

docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Fallo al desplegar la aplicacion
    pause
    exit /b 1
)
echo ✓ Aplicacion desplegada
echo.

echo [4/4] Verificando estado...
timeout /t 10 /nobreak >nul
docker-compose ps
echo.

echo ========================================
echo   DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo La aplicacion esta disponible en:
echo   http://localhost:8080
echo.
echo Credenciales de acceso:
echo   Usuario: admin
echo   Password: admin123
echo.
echo Comandos utiles:
echo   Ver logs: docker-compose logs web
echo   Reiniciar: docker-compose restart
echo   Detener:   docker-compose down
echo.
echo Presiona cualquier tecla para abrir la aplicacion...
pause >nul

echo Abriendo navegador...
start http://localhost:8080
echo.
echo ¡Listo! La aplicacion deberia abrirse en tu navegador.
echo Si no se abre automaticamente, ve a: http://localhost:8080
pause
