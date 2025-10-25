// Garden Manager JavaScript Functions

// Complete a care task
function completeTask(taskId) {
    if (!taskId) {
        console.error('Task ID is required');
        return;
    }

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
            // Show success message
            showNotification('Task completed successfully!', 'success');
            // Reload page to update task list
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showNotification('Failed to complete task: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error completing task:', error);
        showNotification('Error completing task. Please try again.', 'error');
    });
}

// Show notification message
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">
                ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
            </span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        min-width: 300px;
        max-width: 500px;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f1b0b7' : '#b8daff'};
        color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
    `;
    
    notification.querySelector('.notification-content').style.cssText = `
        display: flex;
        align-items: center;
        gap: 0.5rem;
    `;
    
    notification.querySelector('.notification-close').style.cssText = `
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        margin-left: auto;
        padding: 0;
        color: inherit;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Plant search functionality
function initPlantSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    // Update URL to trigger search
                    const url = new URL(window.location);
                    if (this.value) {
                        url.searchParams.set('search', this.value);
                    } else {
                        url.searchParams.delete('search');
                    }
                    window.location.href = url.toString();
                }
            }, 500);
        });
    }
}

// Initialize weather icons animation
function animateWeatherIcons() {
    const weatherIcons = document.querySelectorAll('.weather-icon');
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
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        if (button.onclick || button.type === 'submit') {
            button.addEventListener('click', function() {
                if (!this.disabled) {
                    const originalText = this.textContent;
                    this.textContent = 'Loading...';
                    this.disabled = true;
                    
                    // Re-enable after 3 seconds (safety net)
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.disabled = false;
                    }, 3000);
                }
            });
        }
    });
}

// Initialize page features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌱 Garden Manager JavaScript loaded');
    
    // Initialize features
    initPlantSearch();
    animateWeatherIcons();
    addButtonLoading();
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    console.log('✅ Garden Manager features initialized');
});