// ===== MAIN JAVASCRIPT FILE =====

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    initializeTooltips();
    initializeAlerts();
    initializeForms();
    initializeAnimations();
    initializeNotifications();
    initializeCharts();
    initializeFileUploads();
    initializeModals();
    initializeTables();
    initializeTheme();
}

// ===== TOOLTIPS =====
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ===== ALERTS =====
function initializeAlerts() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
    
    // Add close button functionality
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('alert-close')) {
            const alert = e.target.closest('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }
    });
}

// ===== FORMS =====
function initializeForms() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-save form data
    const autoSaveForms = document.querySelectorAll('[data-autosave]');
    autoSaveForms.forEach(form => {
        const formId = form.getAttribute('data-autosave');
        loadFormData(form, formId);
        
        form.addEventListener('input', debounce(() => {
            saveFormData(form, formId);
        }, 1000));
    });
    
    // Character counters for textareas
    const textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('data-max-length');
        addCharacterCounter(textarea, maxLength);
    });
    
    // Auto-resize textareas
    const autoResizeTextareas = document.querySelectorAll('textarea[data-auto-resize]');
    autoResizeTextareas.forEach(textarea => {
        autoResizeTextarea(textarea);
    });
}

// ===== ANIMATIONS =====
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements with animation classes
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(el => observer.observe(el));
    
    // Stagger animations for lists
    const staggeredLists = document.querySelectorAll('.stagger-animation');
    staggeredLists.forEach(list => {
        const items = list.querySelectorAll('.stagger-item');
        items.forEach((item, index) => {
            item.style.animationDelay = `${index * 0.1}s`;
        });
    });
}

// ===== NOTIFICATIONS =====
function initializeNotifications() {
    // Real-time notification updates
    if (window.WebSocket) {
        connectWebSocket();
    }
    
    // Notification sound
    const notificationSound = new Audio('/static/sounds/notification.mp3');
    
    // Show notification
    window.showNotification = function(title, message, type = 'info') {
        const notification = createNotificationElement(title, message, type);
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            removeNotification(notification);
        }, 5000);
        
        // Play sound
        try {
            notificationSound.play();
        } catch (e) {
            console.log('Could not play notification sound');
        }
    };
    
    // Mark notifications as read
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('mark-notification-read')) {
            const notificationId = e.target.getAttribute('data-notification-id');
            markNotificationAsRead(notificationId);
        }
    });
}

// ===== CHARTS =====
function initializeCharts() {
    // Initialize Chart.js charts
    const chartElements = document.querySelectorAll('.chart');
    chartElements.forEach(element => {
        const ctx = element.getContext('2d');
        const chartType = element.getAttribute('data-chart-type');
        const chartData = JSON.parse(element.getAttribute('data-chart-data'));
        
        new Chart(ctx, {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    });
}

// ===== FILE UPLOADS =====
function initializeFileUploads() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    uploadAreas.forEach(area => {
        initializeUploadArea(area);
    });
}

function initializeUploadArea(area) {
    const fileInput = area.querySelector('input[type="file"]');
    const dropZone = area.querySelector('.drop-zone');
    
    if (!fileInput || !dropZone) return;
    
    // Drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropZone.classList.add('drag-over');
    }
    
    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    }
    
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

// ===== MODALS =====
function initializeModals() {
    // Auto-focus first input in modals
    document.addEventListener('shown.bs.modal', function(e) {
        const modal = e.target;
        const firstInput = modal.querySelector('input, textarea, select');
        if (firstInput) {
            firstInput.focus();
        }
    });
    
    // Confirm dialogs
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };
}

// ===== TABLES =====
function initializeTables() {
    // Sortable tables
    const sortableTables = document.querySelectorAll('.sortable-table');
    sortableTables.forEach(table => {
        makeTableSortable(table);
    });
    
    // Searchable tables
    const searchableTables = document.querySelectorAll('.searchable-table');
    searchableTables.forEach(table => {
        addTableSearch(table);
    });
}

// ===== THEME =====
function initializeTheme() {
    // Dark mode toggle
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.classList.add(savedTheme);
    }
}

// ===== UTILITY FUNCTIONS =====

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Auto-resize textarea
function autoResizeTextarea(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
}

// Add character counter
function addCharacterCounter(textarea, maxLength) {
    const counter = document.createElement('div');
    counter.className = 'character-counter';
    counter.style.fontSize = '0.8rem';
    counter.style.color = '#666';
    counter.style.textAlign = 'right';
    counter.style.marginTop = '0.25rem';
    
    textarea.parentNode.appendChild(counter);
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${textarea.value.length} / ${maxLength} caracteres`;
        
        if (remaining < 50) {
            counter.style.color = '#dc3545';
        } else if (remaining < 100) {
            counter.style.color = '#ffc107';
        } else {
            counter.style.color = '#666';
        }
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}

// Save form data to localStorage
function saveFormData(form, formId) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem(`form_${formId}`, JSON.stringify(data));
}

// Load form data from localStorage
function loadFormData(form, formId) {
    const savedData = localStorage.getItem(`form_${formId}`);
    if (savedData) {
        const data = JSON.parse(savedData);
        
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });
    }
}

// Create notification element
function createNotificationElement(title, message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">
                <i class="fas fa-${getNotificationIcon(type)}"></i>
            </div>
            <div class="notification-text">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="removeNotification(this.parentElement.parentElement)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    return notification;
}

// Get notification icon based on type
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Remove notification
function removeNotification(notification) {
    notification.classList.add('hide');
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// Mark notification as read
function markNotificationAsRead(notificationId) {
    fetch(`/mark-notification-read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove notification from UI
            const notification = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (notification) {
                removeNotification(notification);
            }
        }
    })
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}

// Get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toggle dark mode
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark-mode' : '');
}

// Make table sortable
function makeTableSortable(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            sortTable(table, header);
        });
    });
}

// Sort table by column
function sortTable(table, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const column = header.cellIndex;
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove sort classes from all headers
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add appropriate sort class
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aVal = a.cells[column].textContent.trim();
        const bVal = b.cells[column].textContent.trim();
        
        if (isAscending) {
            return bVal.localeCompare(aVal);
        } else {
            return aVal.localeCompare(bVal);
        }
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// Add search functionality to table
function addTableSearch(table) {
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control mb-3';
    searchInput.placeholder = 'Buscar en la tabla...';
    
    table.parentNode.insertBefore(searchInput, table);
    
    searchInput.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

// Handle file selection
function handleFileSelect(file) {
    // Validate file type and size
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (!allowedTypes.includes(file.type)) {
        showNotification('Error', 'Tipo de archivo no permitido', 'error');
        return;
    }
    
    if (file.size > maxSize) {
        showNotification('Error', 'El archivo es demasiado grande (máximo 10MB)', 'error');
        return;
    }
    
    // Update UI
    const uploadArea = document.querySelector('.upload-area');
    const filePreview = document.querySelector('.file-preview');
    
    if (uploadArea && filePreview) {
        uploadArea.classList.add('d-none');
        filePreview.classList.remove('d-none');
        
        const fileName = filePreview.querySelector('.file-name');
        const fileSize = filePreview.querySelector('.file-size');
        
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = formatFileSize(file.size);
    }
    
    // Enable submit button
    const submitBtn = document.querySelector('#submitBtn');
    if (submitBtn) {
        submitBtn.disabled = false;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Connect to WebSocket for real-time updates
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/notifications/`);
    
    ws.onmessage = function(e) {
        const data = JSON.parse(e.data);
        showNotification(data.title, data.message, data.type);
    };
    
    ws.onclose = function() {
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };
}

// Export functions for global use
window.showNotification = showNotification;
window.removeNotification = removeNotification;
window.confirmAction = confirmAction;
window.toggleDarkMode = toggleDarkMode;

