/**
 * Custom JavaScript for College Attendance Management System
 * Path: static/js/custom.js
 */

// ==================== GLOBAL VARIABLES ====================
let sidebarOpen = true;

// ==================== DOM READY ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('College Attendance Management System Initialized');
    
    // Initialize all components
    initSidebar();
    initTooltips();
    initConfirmations();
    initFormValidation();
    initTableSearch();
    initDatePickers();
    initCharts();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.classList.contains('alert-dismissible')) {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) closeBtn.click();
            }
        });
    }, 5000);
});

// ==================== SIDEBAR FUNCTIONS ====================
function initSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Highlight active menu item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    sidebarOpen = !sidebarOpen;
    
    if (sidebarOpen) {
        sidebar.style.transform = 'translateX(0)';
        mainContent.style.marginLeft = '250px';
    } else {
        sidebar.style.transform = 'translateX(-250px)';
        mainContent.style.marginLeft = '0';
    }
}

// ==================== TOOLTIP INITIALIZATION ====================
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ==================== CONFIRMATION DIALOGS ====================
function initConfirmations() {
    // Delete confirmations
    const deleteButtons = document.querySelectorAll('.btn-danger[title*="Delete"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
}

// ==================== FORM VALIDATION ====================
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// ==================== TABLE SEARCH ====================
function initTableSearch() {
    const searchInputs = document.querySelectorAll('input[id*="search"]');
    
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const filter = this.value.toUpperCase();
            const table = this.closest('.card-body').querySelector('table');
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    let found = false;
                    
                    cells.forEach(cell => {
                        if (cell.textContent.toUpperCase().indexOf(filter) > -1) {
                            found = true;
                        }
                    });
                    
                    row.style.display = found ? '' : 'none';
                });
            }
        });
    });
}

// ==================== DATE PICKER INITIALIZATION ====================
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        // Set max date to today for date of joining, admission, etc.
        if (input.name.includes('date_of')) {
            const today = new Date().toISOString().split('T')[0];
            input.setAttribute('max', today);
        }
    });
}

// ==================== CHART INITIALIZATION ====================
function initCharts() {
    // This function would initialize charts using Chart.js or similar
    // Example: Attendance percentage charts
    const chartContainers = document.querySelectorAll('.attendance-chart');
    
    chartContainers.forEach(container => {
        const percentage = container.dataset.percentage;
        // Create pie chart or bar chart based on percentage
        console.log(`Chart for ${percentage}% attendance`);
    });
}

// ==================== ATTENDANCE MARKING FUNCTIONS ====================
function markAll(status) {
    const radios = document.querySelectorAll('.status-radio');
    
    radios.forEach(radio => {
        if (radio.value === status) {
            radio.checked = true;
        }
    });
    
    showNotification(`All students marked as ${status}`, 'info');
}

function markPresent(studentId) {
    const radio = document.querySelector(`input[name="status_${studentId}"][value="present"]`);
    if (radio) radio.checked = true;
}

function markAbsent(studentId) {
    const radio = document.querySelector(`input[name="status_${studentId}"][value="absent"]`);
    if (radio) radio.checked = true;
}

// ==================== NOTIFICATION SYSTEM ====================
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// ==================== EXPORT FUNCTIONS ====================
function exportToExcel() {
    const table = document.querySelector('table');
    
    if (!table) {
        showNotification('No table found to export', 'warning');
        return;
    }
    
    // This is a placeholder - implement actual Excel export
    showNotification('Preparing Excel export...', 'info');
    
    // You would use a library like xlsx.js for actual implementation
    console.log('Excel export triggered');
}

function exportToPDF() {
    showNotification('Preparing PDF export...', 'info');
    
    // Use jsPDF or similar library
    window.print();
}

function printTable() {
    window.print();
}

// ==================== ATTENDANCE CALCULATOR ====================
function calculateAttendance(totalClasses, attendedClasses) {
    if (totalClasses === 0) return 0;
    return ((attendedClasses / totalClasses) * 100).toFixed(2);
}

function calculateRequiredClasses(currentTotal, currentAttended, targetPercentage) {
    let required = 0;
    let futureTotal = currentTotal;
    let futureAttended = currentAttended;
    
    while ((futureAttended / futureTotal * 100) < targetPercentage && required < 100) {
        futureTotal++;
        futureAttended++;
        required++;
    }
    
    return required;
}

// ==================== FILTER FUNCTIONS ====================
function filterByDay(day) {
    const rows = document.querySelectorAll('[data-day]');
    
    rows.forEach(row => {
        if (day === 'all' || row.dataset.day === day) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function filterByStatus(status) {
    const rows = document.querySelectorAll('[data-status]');
    
    rows.forEach(row => {
        if (status === 'all' || row.dataset.status === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function filterBySemester(semester) {
    const rows = document.querySelectorAll('[data-semester]');
    
    rows.forEach(row => {
        if (semester === 'all' || row.dataset.semester === semester) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// ==================== AJAX FUNCTIONS ====================
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

function ajaxRequest(url, method, data, callback) {
    const csrftoken = getCookie('csrftoken');
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (callback) callback(data);
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred. Please try again.', 'danger');
    });
}

// ==================== LOADING OVERLAY ====================
function showLoading() {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'spinner-overlay';
    overlay.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.remove();
}

// ==================== DATA VALIDATION ====================
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{10}$/;
    return re.test(phone);
}

function validateRollNumber(rollNumber) {
    const re = /^[A-Z0-9]+$/;
    return re.test(rollNumber);
}

// ==================== UTILITY FUNCTIONS ====================
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

function getAttendanceColor(percentage) {
    if (percentage >= 75) return 'success';
    if (percentage >= 65) return 'warning';
    return 'danger';
}

function getAttendanceStatus(percentage) {
    if (percentage >= 75) return 'Good';
    if (percentage >= 65) return 'Warning';
    return 'Critical';
}

// ==================== RESPONSIVE MENU ====================
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// ==================== AUTO-REFRESH ====================
function enableAutoRefresh(interval = 60000) {
    setInterval(() => {
        location.reload();
    }, interval);
}

// ==================== KEYBOARD SHORTCUTS ====================
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save form
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.click();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
});

// ==================== CONSOLE INFORMATION ====================
console.log('%c College Attendance Management System ', 'background: #2c3e50; color: #fff; font-size: 16px; padding: 10px;');
console.log('%c Version: 1.0.0 ', 'background: #3498db; color: #fff; font-size: 12px; padding: 5px;');
console.log('%c Developed for Academic Use ', 'background: #27ae60; color: #fff; font-size: 12px; padding: 5px;');

// Export functions to global scope
window.attendanceSystem = {
    markAll,
    markPresent,
    markAbsent,
    exportToExcel,
    exportToPDF,
    printTable,
    calculateAttendance,
    calculateRequiredClasses,
    filterByDay,
    filterByStatus,
    filterBySemester,
    showNotification,
    showLoading,
    hideLoading
};