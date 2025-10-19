from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import zipfile
import tempfile
import schedule
import time
import threading
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu-clave-secreta-muy-segura')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestion_documental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de email
EMAIL_SENDER = os.getenv('EMAIL_SENDER', "estadisticatessa@gmail.com")
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', "rxcd epqr gebp myhj")

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_SENDER
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD

# Configuración de archivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB máximo por archivo
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar extensiones
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Modelos de base de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relaciones
    assigned_tasks = db.relationship('DocumentTask', foreign_keys='DocumentTask.assigned_to', backref='assigned_user', lazy=True)
    
    def set_password(self, password):
        """Establece la contraseña del usuario"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        return check_password_hash(self.password_hash, password)

class DocumentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    area = db.Column(db.String(100), nullable=False)
    
    # Relaciones
    documents = db.relationship('Document', backref='category', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('document_category.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, expired
    version = db.Column(db.Integer, default=1)
    parent_document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)  # Para versiones
    
    # Relaciones
    uploader = db.relationship('User', backref='uploaded_documents')

class DocumentTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, expired
    notes = db.Column(db.Text)
    total_files_required = db.Column(db.Integer, default=1)  # Número total de archivos requeridos
    files_uploaded = db.Column(db.Integer, default=0)  # Número de archivos subidos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relaciones
    document = db.relationship('Document', backref='tasks')
    assigner = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_tasks_by_me')

class DocumentFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    document = db.relationship('Document', backref='files')
    uploader = db.relationship('User', backref='uploaded_files')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', backref='notifications')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Función helper para verificar si una fecha está vencida
def is_overdue(due_date, status):
    if not due_date or status == 'completed':
        return False
    return due_date < datetime.utcnow()

# Registrar la función en el contexto de Jinja2
@app.template_global()
def is_task_overdue(due_date, status):
    return is_overdue(due_date, status)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Funciones de utilidad para emails
def send_assignment_email(user, task):
    try:
        # Asegurar que el documento esté cargado
        if not task.document:
            document = Document.query.get(task.document_id)
        else:
            document = task.document
            
        msg = Message(
            subject=f'Nueva tarea asignada: {document.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )
        msg.body = f"""
        Hola {user.username},
        
        Se te ha asignado una nueva tarea:
        
        Documento: {document.title}
        Descripción: {document.description}
        Fecha límite: {task.due_date.strftime('%d/%m/%Y') if task.due_date else 'Sin fecha límite'}
        Área: {user.area}
        
        Por favor, inicia sesión en el sistema para ver más detalles y subir el documento.
        
        Saludos,
        Sistema de Gestión Documental
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

def send_reminder_email(user, task):
    try:
        # Asegurar que el documento esté cargado
        if not task.document:
            document = Document.query.get(task.document_id)
        else:
            document = task.document
            
        msg = Message(
            subject=f'Recordatorio: Tarea pendiente - {document.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )
        msg.body = f"""
        Hola {user.username},
        
        Te recordamos que tienes una tarea pendiente:
        
        Documento: {document.title}
        Fecha límite: {task.due_date.strftime('%d/%m/%Y') if task.due_date else 'Sin fecha límite'}
        Estado: {task.status}
        
        Por favor, completa esta tarea lo antes posible.
        
        Saludos,
        Sistema de Gestión Documental
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email de recordatorio: {e}")
        return False

def send_welcome_email(user, password):
    try:
        msg = Message(
            subject='Bienvenido al Sistema de Gestión Documental',
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )
        
        msg.body = f"""
        Hola {user.username},
        
        ¡Bienvenido al Sistema de Gestión Documental!
        
        Tus credenciales de acceso son:
        
        Usuario: {user.username}
        Contraseña: {password}
        Área asignada: {user.area}
        Rol: {user.role}
        
        Puedes acceder al sistema en: http://localhost:8080
        
        Te recomendamos cambiar tu contraseña en tu primer acceso.
        
        Si tienes alguna pregunta, contacta al administrador.
        
        Saludos,
        Sistema de Gestión Documental
        """
        
        mail.send(msg)
        print(f"Email de bienvenida enviado a {user.email}")
        return True
    except Exception as e:
        print(f"Error enviando email de bienvenida: {e}")
        return False

def send_progress_notification(task, uploaded_count):
    try:
        # Obtener el gerente que asignó la tarea
        gerente = User.query.get(task.assigned_by)
        assigned_user = User.query.get(task.assigned_to)
        
        progress_percentage = (uploaded_count / task.total_files_required) * 100
        
        msg = Message(
            subject=f'Progreso de Tarea: {task.document.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[gerente.email]
        )
        
        msg.body = f"""
        Hola {gerente.username},
        
        {assigned_user.username} ha subido {uploaded_count} de {task.total_files_required} archivos requeridos.
        
        Progreso: {progress_percentage:.1f}%
        
        Documento: {task.document.title}
        Área: {task.document.category.area}
        
        Estado: {'Completado' if uploaded_count == task.total_files_required else 'En Progreso'}
        
        Saludos,
        Sistema de Gestión Documental
        """
        
        mail.send(msg)
        print(f"Notificación de progreso enviada a {gerente.email}")
        return True
    except Exception as e:
        print(f"Error enviando notificación de progreso: {e}")
        return False

# Sistema de recordatorios automáticos
def check_overdue_tasks():
    with app.app_context():
        overdue_tasks = DocumentTask.query.filter(
            DocumentTask.due_date < datetime.utcnow(),
            DocumentTask.status.in_(['pending', 'in_progress'])
        ).all()
        
        for task in overdue_tasks:
            # Actualizar estado a expirado
            task.status = 'expired'
            
            # Crear notificación
            notification = Notification(
                user_id=task.assigned_to,
                title='Tarea expirada',
                message=f'La tarea "{task.document.title}" ha expirado.'
            )
            db.session.add(notification)
            
            # Enviar email de recordatorio
            user = User.query.get(task.assigned_to)
            send_reminder_email(user, task)
        
        db.session.commit()

def send_daily_reminders():
    with app.app_context():
        # Enviar recordatorios para tareas que vencen en 3 días
        three_days_from_now = datetime.utcnow() + timedelta(days=3)
        upcoming_tasks = DocumentTask.query.filter(
            DocumentTask.due_date <= three_days_from_now,
            DocumentTask.due_date > datetime.utcnow(),
            DocumentTask.status.in_(['pending', 'in_progress'])
        ).all()
        
        for task in upcoming_tasks:
            user = User.query.get(task.assigned_to)
            send_reminder_email(user, task)

# Configurar tareas programadas
schedule.every().day.at("09:00").do(send_daily_reminders)
schedule.every().hour.do(check_overdue_tasks)

def run_scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Error en scheduler: {e}")
        time.sleep(60)

# Iniciar scheduler en un hilo separado
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Rutas de la aplicación
@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if current_user.role == 'gerente':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    
    # Si es POST, redirigir al login
    if request.method == 'POST':
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'error')
                return render_template('login.html')
            
            # Actualizar última conexión
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            flash('¡Inicio de sesión exitoso!', 'success')
            
            if user.role == 'gerente':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/api/task/<int:task_id>/details')
@login_required
def get_task_details(task_id):
    """Obtener detalles de una tarea específica"""
    if current_user.role != 'gerente':
        return jsonify({'error': 'No tienes permisos para acceder a esta información'}), 403
    
    task = DocumentTask.query.get_or_404(task_id)
    
    # Obtener información del usuario asignado
    assigned_user = User.query.get(task.assigned_to) if task.assigned_to else None
    
    # Obtener información del documento
    document = Document.query.get(task.document_id) if task.document_id else None
    
    # Obtener archivos asociados
    files = DocumentFile.query.filter_by(document_id=task.document_id).all()
    
    # Obtener notificaciones relacionadas (solo del usuario asignado si existe)
    notifications = []
    if task.assigned_to:
        notifications = Notification.query.filter_by(user_id=task.assigned_to).order_by(Notification.created_at.desc()).limit(5).all()
    
    task_details = {
        'id': task.id,
        'title': document.title if document else 'Sin título',
        'description': document.description if document else task.notes or 'Sin descripción',
        'status': task.status,
        'priority': 'media',  # Valor por defecto ya que no existe en el modelo
        'due_date': task.due_date.strftime('%d/%m/%Y %H:%M') if task.due_date else None,
        'created_at': task.created_at.strftime('%d/%m/%Y %H:%M'),
        'total_files_required': task.total_files_required,
        'files_uploaded': task.files_uploaded,
        'completion_percentage': round((task.files_uploaded / task.total_files_required * 100), 1) if task.total_files_required > 0 else 0,
        'assigned_user': {
            'id': assigned_user.id,
            'username': assigned_user.username,
            'email': assigned_user.email,
            'area': assigned_user.area
        } if assigned_user else None,
        'document': {
            'id': document.id,
            'title': document.title,
            'description': document.description
        } if document else None,
        'files': [
            {
                'id': file.id,
                'filename': file.filename,
                'file_size': file.file_size,
                'upload_date': file.uploaded_at.strftime('%d/%m/%Y %H:%M'),
                'uploaded_by': User.query.get(file.uploaded_by).username if file.uploaded_by else 'Sistema'
            } for file in files
        ],
        'notifications': [
            {
                'id': notif.id,
                'message': notif.message,
                'created_at': notif.created_at.strftime('%d/%m/%Y %H:%M'),
                'is_read': notif.is_read
            } for notif in notifications
        ]
    }
    
    return jsonify(task_details)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Obtener áreas dinámicamente desde las categorías
    areas = [cat.area for cat in DocumentCategory.query.all()]
    if not areas:  # Si no hay categorías, usar las por defecto
        areas = ['Sanidad Vegetal', 'Seguridad Industrial', 'Producción', 'Bodegas']
    area_stats = {}
    
    for area in areas:
        users_in_area = User.query.filter_by(area=area).count()
        tasks_in_area = DocumentTask.query.join(User, DocumentTask.assigned_to == User.id).filter(User.area == area).count()
        completed_tasks = DocumentTask.query.join(User, DocumentTask.assigned_to == User.id).filter(
            User.area == area,
            DocumentTask.status == 'completed'
        ).count()
        
        area_stats[area] = {
            'users': users_in_area,
            'total_tasks': tasks_in_area,
            'completed_tasks': completed_tasks,
            'completion_rate': round((completed_tasks / tasks_in_area * 100), 1) if tasks_in_area > 0 else 0
        }
    
    # Obtener tareas recientes
    recent_tasks = DocumentTask.query.order_by(DocumentTask.created_at.desc()).limit(10).all()
    
    # Obtener usuarios por área
    users_by_area = {}
    for area in areas:
        users_by_area[area] = User.query.filter_by(area=area).all()
    
    # Obtener notificaciones para el dashboard
    pending_tasks = DocumentTask.query.filter(DocumentTask.status != 'completed').count()
    overdue_tasks = DocumentTask.query.filter(
        DocumentTask.status != 'completed',
        DocumentTask.due_date < datetime.now()
    ).count()
    
    # Tareas pendientes por área
    pending_by_area = {}
    for area in areas:
        pending_count = DocumentTask.query.join(User, DocumentTask.assigned_to == User.id).filter(
            User.area == area,
            DocumentTask.status != 'completed'
        ).count()
        pending_by_area[area] = pending_count
    
    # Notificaciones no leídas
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).count()
    
    # Obtener todas las categorías
    return render_template('admin_dashboard.html', 
                         area_stats=area_stats, 
                         recent_tasks=recent_tasks,
                         users_by_area=users_by_area,
                         pending_tasks=pending_tasks,
                         overdue_tasks=overdue_tasks,
                         pending_by_area=pending_by_area,
                         unread_notifications=unread_notifications)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # Obtener tareas asignadas al usuario
    user_tasks = DocumentTask.query.filter_by(assigned_to=current_user.id).all()
    
    # Obtener notificaciones no leídas
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    # Obtener documentos de la categoría del usuario (para mostrar en su área)
    user_area_documents = Document.query.join(DocumentCategory).filter(DocumentCategory.area == current_user.area).order_by(Document.created_at.desc()).all()
    
    return render_template('user_dashboard.html', 
                         user_tasks=user_tasks,
                         user_area_documents=user_area_documents,
                         unread_notifications=unread_notifications)

@app.route('/admin/assign-task', methods=['GET', 'POST'])
@app.route('/admin/assign-task/<area>', methods=['GET', 'POST'])
@login_required
def assign_task(area=None):
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        document_title = request.form['document_title']
        document_description = request.form.get('document_description', '')
        assigned_to = request.form['assigned_to']
        area = request.form['area']
        due_date_str = request.form.get('due_date')
        notes = request.form.get('notes', '')
        total_files_required = int(request.form.get('total_files_required', 1))
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida', 'error')
                return redirect(url_for('assign_task'))
        
        # Obtener la categoría del área
        category = DocumentCategory.query.filter_by(area=area).first()
        if not category:
            flash('No se encontró la categoría para esta área', 'error')
            return redirect(url_for('assign_task'))
        
        # Crear documento automáticamente
        document = Document(
            title=document_title,
            description=document_description,
            category_id=category.id,
            status='pending'
        )
        
        db.session.add(document)
        db.session.flush()  # Para obtener el ID del documento
        
        # Crear tarea
        task = DocumentTask(
            document_id=document.id,
            assigned_to=assigned_to,
            assigned_by=current_user.id,
            due_date=due_date,
            notes=notes,
            total_files_required=total_files_required,
            files_uploaded=0
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Crear notificación
        notification = Notification(
            user_id=assigned_to,
            title='Nueva tarea asignada',
            message=f'Se te ha asignado una nueva tarea: {document.title}'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        # Enviar email
        user = User.query.get(assigned_to)
        send_assignment_email(user, task)
        
        flash('Tarea asignada exitosamente. El documento se creó automáticamente.', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Obtener usuarios y áreas para el formulario
    if area:
        # Filtrar usuarios solo del área específica
        users = User.query.filter_by(role='jefe_area', area=area).all()
        selected_area = area
    else:
        # Mostrar todos los usuarios si no se especifica área
        users = User.query.filter_by(role='jefe_area').all()
        selected_area = None
    
    areas = [cat.area for cat in DocumentCategory.query.all()]
    
    return render_template('assign_task.html', users=users, areas=areas, selected_area=selected_area)

@app.route('/upload-document/<int:task_id>', methods=['GET', 'POST'])
@login_required
def upload_document(task_id):
    task = DocumentTask.query.get_or_404(task_id)
    
    if task.assigned_to != current_user.id:
        flash('No tienes permisos para esta tarea', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        files = request.files.getlist('files')  # Cambiar a múltiples archivos
        
        if not files or all(f.filename == '' for f in files):
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('upload_document', task_id=task_id))
        
        uploaded_count = 0
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                unique_filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Crear registro de archivo
                document_file = DocumentFile(
                    document_id=task.document_id,
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    file_type=file.content_type,
                    uploaded_by=current_user.id
                )
                
                db.session.add(document_file)
                uploaded_count += 1
        
        if uploaded_count == 0:
            flash('No se pudo subir ningún archivo válido', 'error')
            return redirect(url_for('upload_document', task_id=task_id))
        
        # Recalcular contador de archivos subidos basado en los archivos reales
        actual_files_count = DocumentFile.query.filter_by(document_id=task.document_id).count()
        task.files_uploaded = actual_files_count
        
        # Actualizar estado de la tarea
        if task.files_uploaded >= task.total_files_required:
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.document.status = 'completed'
        else:
            task.status = 'in_progress'
        
        task.document.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Enviar notificación de progreso al gerente
        send_progress_notification(task, task.files_uploaded)
        
        if task.status == 'completed':
            flash(f'¡Tarea completada! Se subieron {uploaded_count} archivos. Total: {task.files_uploaded}/{task.total_files_required}', 'success')
        else:
            flash(f'Se subieron {uploaded_count} archivos. Progreso: {task.files_uploaded}/{task.total_files_required}', 'info')
        
        return redirect(url_for('user_dashboard'))
    
    return render_template('upload_document.html', task=task)

@app.route('/admin/create-document', methods=['GET', 'POST'])
@login_required
def create_document():
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = request.form['category_id']
        
        document = Document(
            title=title,
            description=description,
            category_id=category_id
        )
        
        db.session.add(document)
        db.session.commit()
        
        flash('Documento creado exitosamente', 'success')
        return redirect(url_for('admin_dashboard'))
    
    categories = DocumentCategory.query.all()
    return render_template('create_document.html', categories=categories)

@app.route('/admin/create-category', methods=['GET', 'POST'])
@login_required
def create_category():
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        area = request.form['area']
        
        category = DocumentCategory(
            name=name,
            description=description,
            area=area
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Categoría creada exitosamente', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_category.html')

@app.route('/mark-notification-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('No tienes permisos para esta notificación', 'error')
        return redirect(url_for('user_dashboard'))
    
    notification.is_read = True
    db.session.commit()
    
    return redirect(url_for('user_dashboard'))

@app.route('/admin/refresh-db')
@login_required
def refresh_database():
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Limpiar todas las sesiones
        db.session.remove()
        db.session.close()
        
        # Recrear las tablas
        db.drop_all()
        db.create_all()
        
        # Reinicializar datos
        init_db()
        
        flash('Base de datos reinicializada correctamente', 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f'Error al reinicializar la base de datos: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/sync-counters')
@login_required
def sync_counters():
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    try:
        sync_file_counters()
        flash('Contadores sincronizados correctamente', 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f'Error al sincronizar contadores: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        task = DocumentTask.query.get_or_404(task_id)
        
        # Obtener información antes de eliminar para el redirect
        area = task.document.category.area
        
        # Eliminar archivos físicos asociados
        files = DocumentFile.query.filter_by(document_id=task.document_id).all()
        for file_record in files:
            if file_record.file_path and os.path.exists(file_record.file_path):
                try:
                    os.remove(file_record.file_path)
                except:
                    pass  # Ignorar errores de archivos no encontrados
        
        # Eliminar registros de la base de datos
        DocumentFile.query.filter_by(document_id=task.document_id).delete()
        db.session.delete(task)
        db.session.delete(task.document)
        db.session.commit()
        
        flash('Tarea eliminada exitosamente', 'success')
        return redirect(url_for('view_folder', area=area))
        
    except Exception as e:
        flash(f'Error al eliminar la tarea: {str(e)}', 'error')
        db.session.rollback()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Obtener áreas disponibles dinámicamente
    available_areas = [cat.area for cat in DocumentCategory.query.all()]
    if not available_areas:  # Si no hay categorías, usar las por defecto
        available_areas = ['Sanidad Vegetal', 'Seguridad Industrial', 'Producción', 'Bodegas']
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        area = request.form['area']
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return render_template('create_user.html', available_areas=available_areas)
        
        if User.query.filter_by(email=email).first():
            flash('El email ya está en uso', 'error')
            return render_template('create_user.html', available_areas=available_areas)
        
        # Crear nuevo usuario
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            area=area,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Enviar email con credenciales
        send_welcome_email(user, password)
        
        flash(f'Usuario {username} creado exitosamente. Se envió un email con las credenciales.', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('create_user.html', available_areas=available_areas)

@app.route('/admin/toggle-user/<int:user_id>')
@login_required
def toggle_user(user_id):
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    
    if user_id == current_user.id:
        flash('No puedes desactivar tu propia cuenta', 'error')
        return redirect(url_for('manage_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.username} {status} exitosamente', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/reset-password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def reset_user_password(user_id):
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash(f'Contraseña de {user.username} actualizada exitosamente', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('reset_password.html', user=user)

@app.route('/admin/folder/<area>')
@login_required
def view_folder(area):
    if current_user.role != 'gerente':
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Obtener documentos de esta área
    area_documents = Document.query.join(DocumentCategory).filter(DocumentCategory.area == area).all()
    
    # Obtener tareas de esta área
    area_tasks = DocumentTask.query.join(User, DocumentTask.assigned_to == User.id).filter(User.area == area).order_by(DocumentTask.created_at.desc()).all()
    
    # Obtener usuarios de esta área
    area_users = User.query.filter_by(area=area, role='jefe_area').all()
    
    return render_template('folder_view.html', 
                         area=area, 
                         documents=area_documents, 
                         tasks=area_tasks, 
                         users=area_users)

@app.route('/admin/request-correction/<int:document_id>', methods=['GET', 'POST'])
@login_required
def request_correction(document_id):
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    
    document = Document.query.get_or_404(document_id)
    
    if request.method == 'POST':
        correction_notes = request.form['correction_notes']
        
        # Obtener la tarea actual
        current_task = DocumentTask.query.filter_by(document_id=document.id).first()
        
        if current_task:
            # Actualizar la tarea existente con la solicitud de corrección
            current_task.notes = f"Corrección solicitada: {correction_notes}"
            current_task.status = 'pending'
            current_task.files_uploaded = 0  # Resetear contador para nueva subida
            
            # Eliminar archivos existentes si se solicita corrección completa
            existing_files = DocumentFile.query.filter_by(document_id=document.id).all()
            for file_record in existing_files:
                if file_record.file_path and os.path.exists(file_record.file_path):
                    os.remove(file_record.file_path)
                db.session.delete(file_record)
            
            # Actualizar estado del documento
            document.status = 'pending'
        else:
            # Crear nueva tarea de corrección
            current_task = DocumentTask(
                document_id=document.id,
                assigned_to=document.uploaded_by,
                assigned_by=current_user.id,
                notes=f"Corrección solicitada: {correction_notes}",
                status='pending',
                total_files_required=1,
                files_uploaded=0
            )
            db.session.add(current_task)
        
        # Crear notificación
        notification = Notification(
            user_id=current_task.assigned_to,
            title='Corrección solicitada',
            message=f'Se solicita corrección para el documento: {document.title}. Notas: {correction_notes}'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        # Enviar email de corrección
        send_correction_email(current_task, correction_notes)
        
        flash('Solicitud de corrección enviada exitosamente', 'success')
        return redirect(url_for('view_folder', area=document.category.area))
    
    return render_template('request_correction.html', document=document)

def send_correction_email(task, correction_notes):
    """Envía email al usuario cuando se solicita una corrección"""
    try:
        assigned_user = User.query.get(task.assigned_to)
        
        msg = Message(
            subject=f'Corrección Solicitada: {task.document.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[assigned_user.email]
        )
        
        msg.body = f"""
        Hola {assigned_user.username},
        
        Se ha solicitado una corrección para el documento que tienes asignado.
        
        Documento: {task.document.title}
        Área: {task.document.category.area}
        
        Notas de corrección:
        {correction_notes}
        
        Por favor, accede al sistema y realiza las correcciones solicitadas.
        
        Puedes eliminar archivos incorrectos y subir las versiones corregidas.
        
        Saludos,
        Sistema de Gestión Documental
        """
        
        mail.send(msg)
        print(f"Email de corrección enviado a {assigned_user.email}")
        return True
    except Exception as e:
        print(f"Error enviando email de corrección: {e}")
        return False

@app.route('/admin/create-area', methods=['GET', 'POST'])
@login_required
def create_area():
    if current_user.role != 'gerente':
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        area_name = request.form['area_name']
        area_description = request.form['area_description']
        assigned_user_id = request.form.get('assigned_user_id')
        
        # Crear categoría automática para el área
        category = DocumentCategory(
            name=f'Documentos de {area_name}',
            area=area_name,
            description=area_description or f'Documentos y archivos del área de {area_name}'
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Área "{area_name}" creada exitosamente', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Obtener áreas existentes para mostrar
    existing_areas = [cat.area for cat in DocumentCategory.query.all()]
    
    return render_template('create_area.html', existing_areas=existing_areas)

@app.route('/download/<int:document_id>')
@login_required
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Si el documento tiene archivos múltiples, mostrar lista
    if document.files:
        return render_template('download_files.html', document=document)
    
    # Si tiene archivo único (compatibilidad hacia atrás)
    if document.file_path and os.path.exists(document.file_path):
        return send_file(document.file_path, as_attachment=True, download_name=document.filename)
    else:
        flash('El archivo no existe', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/download/file/<int:file_id>')
@login_required
def download_single_file(file_id):
    file_record = DocumentFile.query.get_or_404(file_id)
    
    if file_record.file_path and os.path.exists(file_record.file_path):
        return send_file(file_record.file_path, as_attachment=True, download_name=file_record.original_filename)
    else:
        flash('El archivo no existe', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/download/task/<int:task_id>')
@login_required
def download_task_files(task_id):
    task = DocumentTask.query.get_or_404(task_id)
    
    # Verificar permisos (solo el gerente o el usuario asignado puede descargar)
    if current_user.role != 'gerente' and task.assigned_to != current_user.id:
        flash('No tienes permisos para descargar estos archivos', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Obtener todos los archivos de la tarea
    files = DocumentFile.query.filter_by(document_id=task.document_id).all()
    
    if not files:
        flash('No hay archivos para descargar', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Crear archivo ZIP temporal
    temp_dir = tempfile.mkdtemp()
    zip_filename = f"{task.document.category.area}_{task.document.title}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    
    # Limpiar nombre de archivo para que sea válido
    zip_filename = "".join(c for c in zip_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_record in files:
                if file_record.file_path and os.path.exists(file_record.file_path):
                    # Agregar archivo al ZIP con su nombre original
                    zipf.write(file_record.file_path, file_record.original_filename)
        
        # Enviar el archivo ZIP
        return send_file(
            zip_path, 
            as_attachment=True, 
            download_name=zip_filename,
            mimetype='application/zip'
        )
    
    except Exception as e:
        flash(f'Error al crear el archivo ZIP: {str(e)}', 'error')
        return redirect(url_for('user_dashboard'))
    
    finally:
        # Limpiar archivo temporal después de un tiempo
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except:
            pass

@app.route('/delete/file/<int:file_id>')
@login_required
def delete_file(file_id):
    file_record = DocumentFile.query.get_or_404(file_id)
    
    # Verificar permisos (solo el usuario que subió el archivo o el gerente)
    if current_user.id != file_record.uploaded_by and current_user.role != 'gerente':
        flash('No tienes permisos para eliminar este archivo', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Obtener la tarea asociada
    task = DocumentTask.query.filter_by(document_id=file_record.document_id).first()
    
    try:
        # Eliminar archivo físico
        if file_record.file_path and os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(file_record)
        
        # Recalcular contador de archivos subidos basado en los archivos reales
        if task:
            actual_files_count = DocumentFile.query.filter_by(document_id=task.document_id).count()
            task.files_uploaded = actual_files_count
            
            # Actualizar estado de la tarea
            if task.files_uploaded < task.total_files_required:
                task.status = 'in_progress' if task.files_uploaded > 0 else 'pending'
                task.document.status = 'pending'
        
        db.session.commit()
        
        flash('Archivo eliminado exitosamente', 'success')
        
        # Enviar notificación al gerente si es el usuario quien elimina
        if current_user.role != 'gerente' and task:
            send_file_deletion_notification(task, file_record.original_filename)
        
    except Exception as e:
        flash(f'Error al eliminar el archivo: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('user_dashboard'))

def send_file_deletion_notification(task, filename):
    """Envía notificación al gerente cuando un usuario elimina un archivo"""
    try:
        gerente = User.query.get(task.assigned_by)
        assigned_user = User.query.get(task.assigned_to)
        
        msg = Message(
            subject=f'Archivo Eliminado: {task.document.title}',
            sender=app.config['MAIL_USERNAME'],
            recipients=[gerente.email]
        )
        
        msg.body = f"""
        Hola {gerente.username},
        
        {assigned_user.username} ha eliminado un archivo de la tarea asignada.
        
        Archivo eliminado: {filename}
        Documento: {task.document.title}
        Área: {task.document.category.area}
        
        Progreso actual: {task.files_uploaded}/{task.total_files_required} archivos
        
        Saludos,
        Sistema de Gestión Documental
        """
        
        mail.send(msg)
        print(f"Notificación de eliminación de archivo enviada a {gerente.email}")
        return True
    except Exception as e:
        print(f"Error enviando notificación de eliminación: {e}")
        return False

def sync_file_counters():
    """Sincroniza los contadores de archivos con los archivos reales en la base de datos"""
    try:
        tasks = DocumentTask.query.all()
        for task in tasks:
            actual_count = DocumentFile.query.filter_by(document_id=task.document_id).count()
            if task.files_uploaded != actual_count:
                task.files_uploaded = actual_count
                print(f"Corregido contador para tarea {task.id}: {actual_count} archivos")
        db.session.commit()
        print("Contadores sincronizados correctamente")
    except Exception as e:
        print(f"Error sincronizando contadores: {e}")

# Función para inicializar datos de ejemplo
def init_db():
    with app.app_context():
        db.create_all()
        
        # Crear usuario administrador si no existe
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='david.herrera@tessacorporation.com',
                password_hash=generate_password_hash('admin123'),
                role='gerente',
                area='Administración',
                is_active=True,
                last_login=None
            )
            db.session.add(admin)
        
        # Crear categorías automáticas para cada área
        if not DocumentCategory.query.first():
            areas = ['Sanidad Vegetal', 'Seguridad Industrial', 'Producción', 'Bodegas']
            for area in areas:
                category = DocumentCategory(
                    name=f'Documentos de {area}', 
                    area=area, 
                    description=f'Documentos y archivos del área de {area}'
                )
                db.session.add(category)
        
        # Crear usuarios de ejemplo
        if not User.query.filter_by(username='jefe_sanidad').first():
            users = [
                User(username='jefe_sanidad', email='david.herrera1@live.com', password_hash=generate_password_hash('sanidad123'), role='jefe_area', area='Sanidad Vegetal', is_active=True, last_login=None),
                User(username='jefe_seguridad', email='seguridad@empresa.com', password_hash=generate_password_hash('seguridad123'), role='jefe_area', area='Seguridad Industrial', is_active=True, last_login=None),
                User(username='jefe_produccion', email='produccion@empresa.com', password_hash=generate_password_hash('produccion123'), role='jefe_area', area='Producción', is_active=True, last_login=None),
                User(username='jefe_bodegas', email='bodegas@empresa.com', password_hash=generate_password_hash('bodegas123'), role='jefe_area', area='Bodegas', is_active=True, last_login=None)
            ]
            
            for user in users:
                db.session.add(user)
        
        db.session.commit()
        print("Base de datos inicializada con datos de ejemplo")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8080, host='0.0.0.0')
