#!/bin/bash

# Script de entrada para el contenedor Docker
echo "🚀 Iniciando Sistema de Gestión Documental..."

# Función para inicializar la base de datos SQLite
init_database() {
    echo "🗄️ Inicializando base de datos SQLite..."
    python -c "
from app import app, db, User, DocumentCategory
from werkzeug.security import generate_password_hash
import os

with app.app_context():
    try:
        db.create_all()
        print('✅ Base de datos SQLite inicializada correctamente')
        
        # Crear usuario administrador por defecto si no existe
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='david.herrera@tessacorporation.com', role='gerente', area='Administración')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print('✅ Usuario administrador creado')

        # Crear usuario de área por defecto si no existe
        if not User.query.filter_by(username='jefe_sanidad').first():
            area_user = User(username='jefe_sanidad', email='david.herrera1@live.com', role='jefe_area', area='Sanidad Vegetal')
            area_user.set_password('sanidad123')
            db.session.add(area_user)
            db.session.commit()
            print('✅ Usuario de área creado')

        # Crear áreas por defecto si no existen
        areas = ['Sanidad Vegetal', 'Seguridad Industrial', 'Producción', 'Bodegas']
        for area in areas:
            existing_area = DocumentCategory.query.filter_by(name=area).first()
            if not existing_area:
                new_area = DocumentCategory(name=area, description=f'Documentos y archivos del área de {area}', area=area)
                db.session.add(new_area)
                db.session.commit()
                print(f'✅ Área {area} creada')
                
    except Exception as e:
        print(f'❌ Error inicializando base de datos: {e}')
        exit(1)
"
}

# Función principal
main() {
    # Inicializar la base de datos
    init_database
    
    echo "🎉 Sistema listo para iniciar!"
    
    # Ejecutar el comando principal
    exec "$@"
}

# Ejecutar función principal
main "$@"