# 🚀 Instalación Simple - Sistema de Gestión Documental

## 📋 Instalación en Windows (Solo 3 pasos)

### ✅ Requisitos Previos
- Windows 10/11
- Docker Desktop instalado ([Descargar aquí](https://www.docker.com/products/docker-desktop))

### 🎯 Instalación Ultra Simple

#### Opción 1: Script Automático (Recomendado)
```cmd
# 1. Clonar el repositorio
git clone <tu-repositorio>
cd Gestion_Documental

# 2. Ejecutar instalación automática
desplegar.bat
```

#### Opción 2: PowerShell (Más avanzado)
```powershell
# 1. Clonar el repositorio
git clone <tu-repositorio>
cd Gestion_Documental

# 2. Ejecutar instalación con PowerShell
PowerShell -ExecutionPolicy Bypass -File Desplegar.ps1
```

#### Opción 3: Manual
```cmd
# 1. Crear directorios
mkdir static\uploads
mkdir logs
mkdir instance

# 2. Copiar configuración
copy env.example .env

# 3. Construir y ejecutar
docker-compose build
docker-compose up -d
```

### 🌐 Acceso a la Aplicación

**URL:** `http://localhost:8080`

**Credenciales por defecto:**
- **Administrador:** `admin` / `admin123`
- **Jefe de Área:** `jefe_sanidad` / `sanidad123`

### 📁 Estructura de Archivos

```
Gestion_Documental/
├── static/uploads/          # Archivos subidos por usuarios
├── instance/               # Base de datos SQLite
├── logs/                   # Logs de la aplicación
├── desplegar.bat          # Script de instalación automática
├── Desplegar.ps1          # Script PowerShell avanzado
└── docker-compose.yml     # Configuración Docker
```

### 🔧 Comandos Útiles

```cmd
# Ver estado de contenedores
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Parar la aplicación
docker-compose down

# Reiniciar la aplicación
docker-compose restart

# Actualizar la aplicación
docker-compose pull
docker-compose up -d
```

### 💾 Backup y Restauración

#### Backup Simple
```cmd
# Copiar toda la carpeta del proyecto
xcopy Gestion_Documental Gestion_Documental_Backup /E /I
```

#### Restauración
```cmd
# Simplemente copiar la carpeta de vuelta
xcopy Gestion_Documental_Backup Gestion_Documental /E /I
```

### 🔒 Seguridad

#### Cambiar contraseñas por defecto:
1. Iniciar sesión como administrador
2. Ir a "Gestionar Usuarios"
3. Editar usuario y cambiar contraseña

#### Configurar email:
1. Editar archivo `.env`
2. Cambiar `EMAIL_SENDER` y `EMAIL_PASSWORD`
3. Reiniciar: `docker-compose restart`

### 🚨 Solución de Problemas

#### Error: "Docker no está corriendo"
```cmd
# Iniciar Docker Desktop desde el menú inicio
# Esperar a que aparezca el ícono en la bandeja del sistema
```

#### Error: "Puerto 8080 en uso"
```cmd
# Cambiar puerto en docker-compose.yml
# Cambiar "8080:8080" por "8081:8080"
# Reiniciar: docker-compose restart
```

#### Error: "No se puede acceder a la aplicación"
```cmd
# Verificar que Docker esté corriendo
docker-compose ps

# Ver logs para diagnóstico
docker-compose logs web
```

### 📊 Monitoreo

#### Ver uso de recursos:
```cmd
# Ver uso de CPU y memoria
docker stats
```

#### Ver logs de errores:
```cmd
# Logs de la aplicación
docker-compose logs web

# Logs de nginx (si está habilitado)
docker-compose logs nginx
```

### 🔄 Actualizaciones

#### Actualizar la aplicación:
```cmd
# 1. Parar la aplicación
docker-compose down

# 2. Actualizar código (si es un repositorio)
git pull

# 3. Reconstruir y ejecutar
docker-compose build
docker-compose up -d
```

### 📞 Soporte

Para problemas o preguntas:
1. Revisar logs: `docker-compose logs -f`
2. Verificar configuración en `.env`
3. Comprobar que Docker Desktop esté corriendo
4. Revisar recursos del sistema

### 🎯 Características del Sistema

- ✅ **Base de datos SQLite** - Simple y portable
- ✅ **Interfaz web moderna** - Diseño ejecutivo
- ✅ **Gestión por áreas** - Organización empresarial
- ✅ **Subida de múltiples archivos** - Eficiencia
- ✅ **Notificaciones por email** - Comunicación automática
- ✅ **Sistema de versiones** - Control de cambios
- ✅ **Backup automático** - Seguridad de datos

---

## 🎉 ¡Listo para usar!

**Tu sistema de gestión documental estará funcionando en menos de 5 minutos.**

**URL:** `http://localhost:8080`  
**Admin:** `admin` / `admin123`
