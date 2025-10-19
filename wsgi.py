#!/usr/bin/env python3
"""
WSGI entry point para el servidor de producción
"""
import os
from app import app

if __name__ == "__main__":
    # Configuración para producción
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )