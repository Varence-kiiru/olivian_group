/**
 * Enhanced System Messages and UI Utilities
 * Olivian Group - Professional Solar Solutions
 */

// Form Validation Enhancements
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Show loading state
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Reset after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
        
        // Enhanced field validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name || field.id || 'Field';
    
    // Remove existing validation classes
    field.classList.remove('is-valid', 'is-invalid');
    
    // Remove existing feedback
    const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    let isValid = true;
    let message = '';
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = `${fieldName} is required.`;
    }
    
    // Email validation
    else if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid email address.';
        }
    }
    
    // Phone validation
    else if (field.type === 'tel' && value) {
        const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid phone number.';
        }
    }
    
    // Password validation
    else if (field.type === 'password' && value && field.hasAttribute('minlength')) {
        const minLength = parseInt(field.getAttribute('minlength'));
        if (value.length < minLength) {
            isValid = false;
            message = `Password must be at least ${minLength} characters long.`;
        }
    }
    
    // Number validation
    else if (field.type === 'number' && value) {
        const num = parseFloat(value);
        const min = field.hasAttribute('min') ? parseFloat(field.getAttribute('min')) : null;
        const max = field.hasAttribute('max') ? parseFloat(field.getAttribute('max')) : null;
        
        if (isNaN(num)) {
            isValid = false;
            message = 'Please enter a valid number.';
        } else if (min !== null && num < min) {
            isValid = false;
            message = `Value must be at least ${min}.`;
        } else if (max !== null && num > max) {
            isValid = false;
            message = `Value must not exceed ${max}.`;
        }
    }
    
    // Apply validation styling
    if (isValid) {
        field.classList.add('is-valid');
        if (value) { // Only show valid feedback if there's a value
            addFieldFeedback(field, 'Looks good!', 'valid-feedback');
        }
    } else {
        field.classList.add('is-invalid');
        addFieldFeedback(field, message, 'invalid-feedback');
    }
    
    return isValid;
}

function addFieldFeedback(field, message, className) {
    const feedback = document.createElement('div');
    feedback.className = className;
    feedback.textContent = message;
    field.parentNode.appendChild(feedback);
}

// Enhanced Confirmation Dialogs
function showConfirmDialog(title, message, onConfirm, onCancel = null) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header border-0 pb-0">
                        <h5 class="modal-title fw-bold">${title}</h5>
                    </div>
                    <div class="modal-body">
                        <p class="mb-0">${message}</p>
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary confirm-btn">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal);
        
        modal.querySelector('.confirm-btn').addEventListener('click', () => {
            bsModal.hide();
            if (onConfirm) onConfirm();
            resolve(true);
        });
        
        modal.addEventListener('hidden.bs.modal', () => {
            if (onCancel) onCancel();
            modal.remove();
            resolve(false);
        });
        
        bsModal.show();
    });
}

// Progress Indicators
function createProgressBar(container, percentage = 0, label = '') {
    const progressContainer = document.createElement('div');
    progressContainer.className = 'mb-3';
    progressContainer.innerHTML = `
        ${label ? `<div class="d-flex justify-content-between mb-1"><small>${label}</small><small>${percentage}%</small></div>` : ''}
        <div class="progress" style="height: 8px;">
            <div class="progress-bar bg-primary progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: ${percentage}%"></div>
        </div>
    `;
    
    if (typeof container === 'string') {
        container = document.querySelector(container);
    }
    
    container.appendChild(progressContainer);
    
    return {
        update: (newPercentage, newLabel = label) => {
            const progressBar = progressContainer.querySelector('.progress-bar');
            const labelElement = progressContainer.querySelector('small');
            const percentElement = progressContainer.querySelector('small:last-child');
            
            progressBar.style.width = `${newPercentage}%`;
            if (labelElement && newLabel) labelElement.textContent = newLabel;
            if (percentElement) percentElement.textContent = `${newPercentage}%`;
        },
        remove: () => progressContainer.remove()
    };
}

// Enhanced Error Handling
function handleAjaxError(xhr, textStatus, errorThrown) {
    let message = 'An unexpected error occurred. Please try again.';
    
    if (xhr.status === 0) {
        message = 'Network error. Please check your internet connection.';
    } else if (xhr.status >= 400 && xhr.status < 500) {
        message = 'Invalid request. Please check your input and try again.';
    } else if (xhr.status >= 500) {
        message = 'Server error. Please try again later.';
    }
    
    try {
        const response = JSON.parse(xhr.responseText);
        if (response.message) {
            message = response.message;
        } else if (response.error) {
            message = response.error;
        }
    } catch (e) {
        // Use default message
    }
    
    window.showToast(message, 'error');
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    enhanceFormValidation();
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            if (alert.classList.contains('show')) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }
        });
    }, 5000);
    
    // Enhance delete buttons with confirmation
    document.querySelectorAll('[data-confirm-delete]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            
            showConfirmDialog(
                'Confirm Deletion',
                message,
                () => {
                    // Proceed with the action
                    if (this.tagName === 'A') {
                        window.location.href = this.href;
                    } else if (this.form) {
                        this.form.submit();
                    }
                }
            );
        });
    });
});

// Make functions globally available
window.showConfirmDialog = showConfirmDialog;
window.createProgressBar = createProgressBar;
window.handleAjaxError = handleAjaxError;
window.validateField = validateField;
