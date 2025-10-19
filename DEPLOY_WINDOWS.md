# 🚀 Despliegue en Windows Server

## 📋 Requisitos Previos

### 1. Instalar Docker Desktop
- Descargar desde: https://www.docker.com/products/docker-desktop
- Instalar y reiniciar la PC
- Verificar instalación:
  ```cmd
  docker --version
  docker-compose --version
  ```

### 2. Verificar Puerto 8080
```cmd
netstat -an | findstr :8080
```
Si está ocupado, cambiar en `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Cambiar 8080 por 8081
```

## 🚀 Método 1: Clonar desde Git (Recomendado)

### Paso 1: Clonar repositorio
```cmd
git clone https://github.com/tu-usuario/Gestion_Documental.git
cd Gestion_Documental
```

### Paso 2: Desplegar
```cmd
docker-compose up -d
```

### Paso 3: Verificar
- Abrir navegador: `http://localhost:8080`
- Login: `admin` / `admin123`

## 📦 Método 2: Transferir archivos

### Paso 1: Comprimir en máquina origen
```bash
# En Linux/Mac:
tar -czf gestion_documental.tar.gz .
```

### Paso 2: Transferir a Windows
- Copiar archivo comprimido
- Extraer en carpeta deseada

### Paso 3: Desplegar
```cmd
cd gestion_documental
docker-compose up -d
```

## 🔧 Comandos Útiles

### Ver estado del contenedor
```cmd
docker-compose ps
```

### Ver logs
```cmd
docker-compose logs web
```

### Reiniciar aplicación
```cmd
docker-compose restart
```

### Detener aplicación
```cmd
docker-compose down
```

### Actualizar aplicación
```cmd
git pull
docker-compose build
docker-compose up -d
```

## 🛡️ Seguridad

### Cambiar credenciales por defecto
1. Editar `docker-entrypoint.sh`
2. Cambiar passwords:
   - `admin123` → `tu_password_seguro`
   - `sanidad123` → `otro_password_seguro`

### Configurar firewall
- Permitir puerto 8080 (o el que uses)
- Restringir acceso por IP si es necesario

## 📊 Monitoreo

### Ver uso de recursos
```cmd
docker stats
```

### Backup de base de datos
```cmd
# La base de datos está en: ./instance/gestion_documental.db
# Hacer backup regular de esta carpeta
```

## 🆘 Solución de Problemas

### Error: Puerto ocupado
```cmd
# Cambiar puerto en docker-compose.yml
ports:
  - "8081:8080"
```

### Error: Docker no responde
```cmd
# Reiniciar Docker Desktop
# O reiniciar servicio:
net stop com.docker.service
net start com.docker.service
```

### Error: Memoria insuficiente
```cmd
# En Docker Desktop > Settings > Resources
# Aumentar memoria asignada
```

## 📞 Soporte

Si hay problemas:
1. Verificar logs: `docker-compose logs web`
2. Verificar estado: `docker-compose ps`
3. Reiniciar: `docker-compose restart`
