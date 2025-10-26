// Garden Manager JavaScript Functions

// ============================================================================
// Task Completion
// ============================================================================

// Complete a care task
function completeTask(taskId) {
    if (!taskId) {
        console.error('Task ID is required');
        return;
    }

    // Show loading state
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="loading"></span> Completing...';

    fetch('/api/complete_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            task_id: taskId,
            notes: 'Completed via web app'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('✅ Task completed successfully!', 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showNotification('❌ Failed to complete task: ' + (data.message || 'Unknown error'), 'error');
            button.disabled = false;
            button.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('Error completing task:', error);
        showNotification('❌ Error completing task. Please try again.', 'error');
        button.disabled = false;
        button.textContent = originalText;
    });
}

// ============================================================================
// Notifications / Toasts
// ============================================================================

// Show notification message with enhanced styling
function showNotification(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icons[type] || icons.info}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()" aria-label="Close notification">×</button>
        </div>
    `;
    
    // Styling
    const colors = {
        success: { bg: '#d4edda', border: '#c3e6cb', color: '#155724' },
        error: { bg: '#f8d7da', border: '#f1b0b7', color: '#721c24' },
        warning: { bg: '#fff3cd', border: '#ffeaa7', color: '#856404' },
        info: { bg: '#d1ecf1', border: '#b8daff', color: '#0c5460' }
    };
    
    const colorScheme = colors[type] || colors.info;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 320px;
        max-width: 500px;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        background: ${colorScheme.bg};
        border: 2px solid ${colorScheme.border};
        color: ${colorScheme.color};
        animation: slideInRight 0.3s ease;
    `;
    
    notification.querySelector('.notification-content').style.cssText = `
        display: flex;
        align-items: center;
        gap: 0.75rem;
    `;
    
    notification.querySelector('.notification-icon').style.cssText = `
        font-size: 1.5rem;
    `;
    
    notification.querySelector('.notification-message').style.cssText = `
        flex: 1;
        line-height: 1.5;
    `;
    
    notification.querySelector('.notification-close').style.cssText = `
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        color: inherit;
        opacity: 0.7;
        transition: opacity 0.2s;
    `;
    
    // Add to page
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    `;
    document.body.appendChild(container);
    return container;
}

// ============================================================================
// Search and Autocomplete
// ============================================================================

// Plant search functionality with debouncing
function initPlantSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        
        // Add search icon
        const wrapper = searchInput.parentElement;
        wrapper.style.position = 'relative';
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Show loading indicator
            this.style.backgroundImage = "url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"20\" height=\"20\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"10\" fill=\"none\" stroke=\"%234A7C59\" stroke-width=\"2\"/></svg>')";
            this.style.backgroundRepeat = 'no-repeat';
            this.style.backgroundPosition = 'right 10px center';
            
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    const url = new URL(window.location);
                    if (this.value) {
                        url.searchParams.set('search', this.value);
                    } else {
                        url.searchParams.delete('search');
                    }
                    window.location.href = url.toString();
                }
            }, 600);
        });
        
        // Add clear button
        if (searchInput.value) {
            addClearButton(searchInput);
        }
    }
}

function addClearButton(input) {
    if (input.nextElementSibling?.classList.contains('clear-search')) return;
    
    const clearBtn = document.createElement('button');
    clearBtn.innerHTML = '×';
    clearBtn.className = 'clear-search';
    clearBtn.setAttribute('aria-label', 'Clear search');
    clearBtn.style.cssText = `
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #999;
        padding: 0 5px;
    `;
    clearBtn.onclick = () => {
        input.value = '';
        input.focus();
        const url = new URL(window.location);
        url.searchParams.delete('search');
        window.location.href = url.toString();
    };
    input.parentElement.style.position = 'relative';
    input.parentElement.appendChild(clearBtn);
}

// ============================================================================
// UI Enhancements
// ============================================================================

// Initialize weather icons animation
function animateWeatherIcons() {
    const weatherIcons = document.querySelectorAll('.weather-icon, [role="img"]');
    weatherIcons.forEach(icon => {
        icon.style.transition = 'transform 0.3s ease';
        
        icon.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.2) rotate(5deg)';
        });
        
        icon.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
    });
}

// Add loading states to buttons
function addButtonLoading() {
    const buttons = document.querySelectorAll('.btn[type="submit"]');
    buttons.forEach(button => {
        const form = button.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                if (!button.disabled) {
                    const originalText = button.innerHTML;
                    button.innerHTML = '<span class="loading"></span> Loading...';
                    button.disabled = true;
                    
                    // Re-enable after 10 seconds as safety net
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.disabled = false;
                    }, 10000);
                }
            });
        }
    });
}

// Add smooth scrolling to anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Update URL without jumping
                history.pushState(null, null, href);
            }
        });
    });
}

// Keyboard shortcuts
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Alt+D: Dashboard
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/';
        }
        // Alt+P: Plants
        if (e.altKey && e.key === 'p') {
            e.preventDefault();
            window.location.href = '/plants';
        }
        // Alt+G: Garden
        if (e.altKey && e.key === 'g') {
            e.preventDefault();
            window.location.href = '/garden';
        }
        // Alt+C: Care
        if (e.altKey && e.key === 'c') {
            e.preventDefault();
            window.location.href = '/care';
        }
        // Alt+W: Weather
        if (e.altKey && e.key === 'w') {
            e.preventDefault();
            window.location.href = '/weather';
        }
        // Escape: Clear search
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('search');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.value = '';
                searchInput.blur();
            }
        }
    });
}

// Add tooltips to elements with title attribute
function enhanceTooltips() {
    const elementsWithTitle = document.querySelectorAll('[title]');
    elementsWithTitle.forEach(element => {
        const title = element.getAttribute('title');
        element.setAttribute('data-tooltip', title);
        element.classList.add('tooltip');
        element.removeAttribute('title'); // Prevent default browser tooltip
    });
}

// Confirm before destructive actions
function initConfirmDialogs() {
    const destructiveActions = document.querySelectorAll('[data-confirm]');
    destructiveActions.forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
}

// Add loading indicator for page transitions
function initPageLoadingIndicator() {
    // Show loading indicator on navigation
    window.addEventListener('beforeunload', function() {
        document.body.style.opacity = '0.7';
        document.body.style.pointerEvents = 'none';
    });
}

// ============================================================================
// CSS Animations
// ============================================================================

// Add CSS for animations if not in stylesheet
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.6s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// Initialization
// ============================================================================

// Initialize all features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌱 Planted JavaScript initializing...');
    
    try {
        // Core features
        initPlantSearch();
        animateWeatherIcons();
        addButtonLoading();
        initSmoothScrolling();
        initKeyboardShortcuts();
        enhanceTooltips();
        initConfirmDialogs();
        initPageLoadingIndicator();
        addAnimationStyles();
        
        console.log('✅ Planted features initialized successfully');
        
        // Show welcome message on first visit
        if (!sessionStorage.getItem('welcomed')) {
            setTimeout(() => {
                showNotification('🌱 Welcome to Planted! Press Alt+? for keyboard shortcuts.', 'info');
                sessionStorage.setItem('welcomed', 'true');
            }, 1000);
        }
    } catch (error) {
        console.error('❌ Error initializing features:', error);
    }
});