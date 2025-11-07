'use strict';

// ============================================================================
// Form Validation Module
// ============================================================================

/**
 * Client-side form validation with real-time feedback
 * Provides HTML5 and custom JavaScript validation for all forms
 */

// Validation rules and patterns
const ValidationRules = {
    username: {
        minLength: 3,
        maxLength: 50,
        pattern: /^[a-zA-Z0-9_-]+$/,
        message: 'Username must be 3-50 characters and contain only letters, numbers, underscores, and hyphens'
    },
    email: {
        pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        message: 'Please enter a valid email address'
    },
    password: {
        minLength: 6,
        message: 'Password must be at least 6 characters long'
    },
    passwordStrength: {
        weak: /^.{6,}$/,
        medium: /^(?=.*[a-z])(?=.*[A-Z]).{6,}$/,
        strong: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
        veryStrong: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{10,}$/
    },
    latitude: {
        min: -90,
        max: 90,
        message: 'Latitude must be between -90 and 90'
    },
    longitude: {
        min: -180,
        max: 180,
        message: 'Longitude must be between -180 and 180'
    },
    usdaZones: {
        pattern: /^([1-9]|1[0-3])(,\s*([1-9]|1[0-3]))*$/,
        message: 'Enter USDA zones as numbers 1-13, separated by commas (e.g., 5,6,7,8,9)'
    }
};

// Validation state tracking
const FormValidationState = new Map();

// ============================================================================
// Core Validation Functions
// ============================================================================

/**
 * Initialize validation for all forms on the page
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Skip forms that opt-out of validation
        if (form.hasAttribute('data-no-validation')) {
            return;
        }
        
        // Initialize validation state for this form
        const formId = form.id || generateFormId(form);
        form.id = formId;
        FormValidationState.set(formId, {
            valid: false,
            fields: new Map()
        });
        
        // Add validation to all inputs
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type !== 'hidden' && input.type !== 'submit') {
                setupFieldValidation(input, formId);
            }
        });
        
        // Add form submit validation
        form.addEventListener('submit', (e) => handleFormSubmit(e, formId));
        
        // Add password confirmation validation if present
        setupPasswordConfirmation(form);
        setupEmailConfirmation(form);
        
        // Initial validation state check
        updateFormValidationState(formId);
    });
}

/**
 * Setup validation for a single field
 */
function setupFieldValidation(field, formId) {
    // Add validation container for error messages
    const container = createValidationContainer(field);
    
    // Add validation on blur (when user leaves field)
    field.addEventListener('blur', () => {
        if (field.value || field.hasAttribute('required')) {
            validateField(field, formId);
        }
    });
    
    // Add real-time validation on input for certain fields
    if (shouldValidateOnInput(field)) {
        field.addEventListener('input', () => {
            if (field.classList.contains('is-invalid') || field.classList.contains('is-valid')) {
                validateField(field, formId);
            }
        });
    }
    
    // Special handling for specific field types
    if (field.name === 'password' && field.id === 'password') {
        field.addEventListener('input', () => showPasswordStrength(field));
    }
}

/**
 * Validate a single field
 */
function validateField(field, formId) {
    const value = field.value.trim();
    const validators = getFieldValidators(field);
    let isValid = true;
    let errorMessage = '';
    
    // Check HTML5 validity first
    if (!field.checkValidity()) {
        isValid = false;
        errorMessage = field.validationMessage || 'Please fill out this field correctly';
    }
    
    // Run custom validators
    if (isValid && validators.length > 0) {
        for (const validator of validators) {
            const result = validator(value, field);
            if (!result.valid) {
                isValid = false;
                errorMessage = result.message;
                break;
            }
        }
    }
    
    // Update UI
    updateFieldUI(field, isValid, errorMessage);
    
    // Update form state
    const formState = FormValidationState.get(formId);
    if (formState) {
        formState.fields.set(field.name, isValid);
        updateFormValidationState(formId);
    }
    
    return isValid;
}

/**
 * Get validators for a specific field
 */
function getFieldValidators(field) {
    const validators = [];
    const type = field.type;
    const name = field.name;
    
    // Email validation
    if (type === 'email' || name === 'email' || name === 'new_email') {
        validators.push((value) => {
            if (!value) return { valid: true };
            const isValid = ValidationRules.email.pattern.test(value);
            return {
                valid: isValid,
                message: ValidationRules.email.message
            };
        });
    }
    
    // Password validation
    if (type === 'password' && (name === 'password' || name === 'new_password')) {
        validators.push((value) => {
            if (!value) return { valid: true };
            const isValid = value.length >= ValidationRules.password.minLength;
            return {
                valid: isValid,
                message: ValidationRules.password.message
            };
        });
    }
    
    // Username validation
    if (name === 'username') {
        validators.push((value) => {
            if (!value) return { valid: true };
            const rules = ValidationRules.username;
            if (value.length < rules.minLength || value.length > rules.maxLength) {
                return { valid: false, message: rules.message };
            }
            if (!rules.pattern.test(value)) {
                return { valid: false, message: rules.message };
            }
            return { valid: true };
        });
    }
    
    // Latitude validation
    if (name === 'latitude') {
        validators.push((value) => {
            if (!value) return { valid: true };
            const num = parseFloat(value);
            const isValid = !isNaN(num) && num >= ValidationRules.latitude.min && num <= ValidationRules.latitude.max;
            return {
                valid: isValid,
                message: ValidationRules.latitude.message
            };
        });
    }
    
    // Longitude validation
    if (name === 'longitude') {
        validators.push((value) => {
            if (!value) return { valid: true };
            const num = parseFloat(value);
            const isValid = !isNaN(num) && num >= ValidationRules.longitude.min && num <= ValidationRules.longitude.max;
            return {
                valid: isValid,
                message: ValidationRules.longitude.message
            };
        });
    }
    
    // USDA zones validation
    if (name === 'climate_zones') {
        validators.push((value) => {
            if (!value) return { valid: true };
            const isValid = ValidationRules.usdaZones.pattern.test(value);
            return {
                valid: isValid,
                message: ValidationRules.usdaZones.message
            };
        });
    }
    
    return validators;
}

/**
 * Update field UI based on validation state
 */
function updateFieldUI(field, isValid, errorMessage) {
    const container = field.closest('.form-group') || field.parentElement;
    const feedback = container.querySelector('.validation-feedback');
    
    // Remove existing validation classes
    field.classList.remove('is-valid', 'is-invalid');
    
    // Add appropriate class
    if (field.value || field.hasAttribute('required')) {
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
        }
    }
    
    // Update feedback message
    if (feedback) {
        if (isValid) {
            feedback.textContent = '';
            feedback.classList.remove('show');
        } else if (errorMessage) {
            feedback.textContent = errorMessage;
            feedback.classList.add('show');
        }
    }
}

/**
 * Create validation feedback container for a field
 */
function createValidationContainer(field) {
    const container = field.closest('.form-group') || field.parentElement;
    
    // Check if validation feedback already exists
    let feedback = container.querySelector('.validation-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'validation-feedback';
        
        // Insert after the field or after the last child if small tag exists
        const small = container.querySelector('small');
        if (small) {
            small.parentNode.insertBefore(feedback, small.nextSibling);
        } else {
            container.appendChild(feedback);
        }
    }
    
    return container;
}

/**
 * Update overall form validation state
 */
function updateFormValidationState(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const state = FormValidationState.get(formId);
    if (!state) return;
    
    // Check if all required fields are filled and valid
    const requiredFields = form.querySelectorAll('[required]');
    let allValid = true;
    
    requiredFields.forEach(field => {
        if (field.type === 'hidden' || field.type === 'submit') return;
        
        // Check if field has value
        if (!field.value) {
            allValid = false;
            return;
        }
        
        // Check validation state
        if (field.classList.contains('is-invalid')) {
            allValid = false;
        }
    });
    
    state.valid = allValid;
    
    // Update submit button state
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = !allValid;
        
        // Add visual feedback to button
        if (allValid) {
            submitBtn.classList.remove('btn-disabled');
        } else {
            submitBtn.classList.add('btn-disabled');
        }
    }
}

/**
 * Handle form submission
 */
function handleFormSubmit(e, formId) {
    const form = e.target;
    const inputs = form.querySelectorAll('input, select, textarea');
    let isValid = true;
    
    // Validate all fields
    inputs.forEach(input => {
        if (input.type !== 'hidden' && input.type !== 'submit') {
            if (!validateField(input, formId)) {
                isValid = false;
            }
        }
    });
    
    // If form is invalid, prevent submission and show error
    if (!isValid) {
        e.preventDefault();
        
        // Scroll to first invalid field
        const firstInvalid = form.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstInvalid.focus();
        }
        
        // Show notification
        if (typeof showNotification === 'function') {
            showNotification('Please fix the errors in the form before submitting', 'error');
        }
        
        return false;
    }
    
    return true;
}

// ============================================================================
// Special Validation Functions
// ============================================================================

/**
 * Setup password confirmation validation
 */
function setupPasswordConfirmation(form) {
    const password = form.querySelector('input[name="password"], input[name="new_password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    
    if (!password || !confirmPassword) return;
    
    const validatePasswordMatch = () => {
        const passwordValue = password.value;
        const confirmValue = confirmPassword.value;
        
        if (!confirmValue) return;
        
        const isValid = passwordValue === confirmValue;
        const errorMessage = isValid ? '' : 'Passwords do not match';
        
        updateFieldUI(confirmPassword, isValid, errorMessage);
    };
    
    password.addEventListener('input', validatePasswordMatch);
    confirmPassword.addEventListener('input', validatePasswordMatch);
    confirmPassword.addEventListener('blur', validatePasswordMatch);
}

/**
 * Setup email confirmation validation
 */
function setupEmailConfirmation(form) {
    const email = form.querySelector('input[name="new_email"]');
    const confirmEmail = form.querySelector('input[name="confirm_email"]');
    
    if (!email || !confirmEmail) return;
    
    const validateEmailMatch = () => {
        const emailValue = email.value;
        const confirmValue = confirmEmail.value;
        
        if (!confirmValue) return;
        
        const isValid = emailValue === confirmValue;
        const errorMessage = isValid ? '' : 'Email addresses do not match';
        
        updateFieldUI(confirmEmail, isValid, errorMessage);
    };
    
    email.addEventListener('input', validateEmailMatch);
    confirmEmail.addEventListener('input', validateEmailMatch);
    confirmEmail.addEventListener('blur', validateEmailMatch);
}

/**
 * Show password strength indicator
 */
function showPasswordStrength(field) {
    const container = field.closest('.form-group') || field.parentElement;
    let strengthIndicator = container.querySelector('.password-strength');
    
    if (!strengthIndicator) {
        strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength';
        
        const feedback = container.querySelector('.validation-feedback');
        if (feedback) {
            container.insertBefore(strengthIndicator, feedback);
        } else {
            container.appendChild(strengthIndicator);
        }
    }
    
    const password = field.value;
    
    if (!password) {
        strengthIndicator.innerHTML = '';
        return;
    }
    
    const rules = ValidationRules.passwordStrength;
    let strength = 'weak';
    let strengthText = 'Weak';
    let color = '#dc3545';
    
    if (rules.veryStrong.test(password)) {
        strength = 'very-strong';
        strengthText = 'Very Strong';
        color = '#28a745';
    } else if (rules.strong.test(password)) {
        strength = 'strong';
        strengthText = 'Strong';
        color = '#28a745';
    } else if (rules.medium.test(password)) {
        strength = 'medium';
        strengthText = 'Medium';
        color = '#ffc107';
    }
    
    strengthIndicator.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
            <div style="flex: 1; height: 4px; background: #e9ecef; border-radius: 2px; overflow: hidden;">
                <div class="strength-bar strength-${strength}" style="height: 100%; background: ${color}; transition: width 0.3s;"></div>
            </div>
            <span style="font-size: 0.85rem; color: ${color}; font-weight: 600;">${strengthText}</span>
        </div>
        <small style="display: block; margin-top: 0.25rem; color: #666;">
            ${getPasswordStrengthTips(password)}
        </small>
    `;
    
    // Animate the strength bar
    const strengthBar = strengthIndicator.querySelector('.strength-bar');
    const width = strength === 'very-strong' ? '100%' : strength === 'strong' ? '75%' : strength === 'medium' ? '50%' : '25%';
    strengthBar.style.width = width;
}

/**
 * Get password strength tips
 */
function getPasswordStrengthTips(password) {
    const tips = [];
    
    if (password.length < 8) {
        tips.push('Use at least 8 characters');
    }
    if (!/[a-z]/.test(password)) {
        tips.push('Add lowercase letters');
    }
    if (!/[A-Z]/.test(password)) {
        tips.push('Add uppercase letters');
    }
    if (!/\d/.test(password)) {
        tips.push('Add numbers');
    }
    if (!/[@$!%*?&]/.test(password)) {
        tips.push('Add special characters (@$!%*?&)');
    }
    
    if (tips.length === 0) {
        return 'Excellent password! 🎉';
    }
    
    return 'Tip: ' + tips.join(', ');
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate a unique form ID
 */
function generateFormId(form) {
    return 'form-' + Math.random().toString(36).substr(2, 9);
}

/**
 * Check if field should validate on input
 */
function shouldValidateOnInput(field) {
    // Real-time validation for certain field types
    const realtimeTypes = ['password', 'email', 'number', 'tel'];
    return realtimeTypes.includes(field.type) || field.name === 'username';
}

// ============================================================================
// CSS Injection for Validation Styles
// ============================================================================

/**
 * Add validation CSS styles
 */
function addValidationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Validation field styles */
        .form-group input.is-valid,
        .form-group select.is-valid,
        .form-group textarea.is-valid {
            border-color: #28a745;
            padding-right: calc(1.5em + 0.75rem);
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2328a745' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
        
        .form-group input.is-invalid,
        .form-group select.is-invalid,
        .form-group textarea.is-invalid {
            border-color: #dc3545;
            padding-right: calc(1.5em + 0.75rem);
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
        
        .form-group input:focus.is-valid,
        .form-group select:focus.is-valid,
        .form-group textarea:focus.is-valid {
            border-color: #28a745;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
        }
        
        .form-group input:focus.is-invalid,
        .form-group select:focus.is-invalid,
        .form-group textarea:focus.is-invalid {
            border-color: #dc3545;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
        }
        
        /* Validation feedback messages */
        .validation-feedback {
            display: none;
            width: 100%;
            margin-top: 0.25rem;
            font-size: 0.875rem;
            color: #dc3545;
        }
        
        .validation-feedback.show {
            display: block;
        }
        
        /* Password strength indicator */
        .password-strength {
            margin-top: 0.5rem;
        }
        
        /* Disabled button state */
        .btn-disabled {
            opacity: 0.65;
            cursor: not-allowed;
        }
        
        /* Smooth transitions */
        input, select, textarea {
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// Initialization
// ============================================================================

// Initialize validation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔒 Form validation initializing...');
    
    try {
        addValidationStyles();
        initFormValidation();
        console.log('✅ Form validation initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing form validation:', error);
    }
});
