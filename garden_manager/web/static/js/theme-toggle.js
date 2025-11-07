'use strict';

// ============================================================================
// Theme Toggle Functionality
// ============================================================================

/**
 * Theme Manager for Dark/Light Mode Toggle
 * Handles:
 * - User preference storage in localStorage
 * - System preference detection
 * - Theme switching with smooth transitions
 * - Accessibility (respects prefers-color-scheme)
 */

(function() {
    const THEME_KEY = 'planted-theme';
    const DARK_MODE_CLASS = 'dark-mode';
    const LIGHT_MODE_CLASS = 'light-mode';
    
    /**
     * Get the current theme from localStorage or system preference
     * @returns {string} 'dark' or 'light'
     */
    function getCurrentTheme() {
        // Check localStorage first for user preference
        const savedTheme = localStorage.getItem(THEME_KEY);
        if (savedTheme) {
            return savedTheme;
        }
        
        // Fall back to system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        // Default to light theme
        return 'light';
    }
    
    /**
     * Apply the theme to the document
     * @param {string} theme - 'dark' or 'light'
     */
    function applyTheme(theme) {
        const body = document.body;
        
        if (theme === 'dark') {
            body.classList.add(DARK_MODE_CLASS);
            body.classList.remove(LIGHT_MODE_CLASS);
        } else {
            body.classList.add(LIGHT_MODE_CLASS);
            body.classList.remove(DARK_MODE_CLASS);
        }
        
        // Update toggle button icon if it exists
        updateToggleButton(theme);
        
        // Update aria-label for accessibility
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
            toggleButton.setAttribute('aria-label', label);
            toggleButton.setAttribute('title', label);
        }
    }
    
    /**
     * Update the theme toggle button appearance
     * @param {string} theme - 'dark' or 'light'
     */
    function updateToggleButton(theme) {
        const toggleButton = document.getElementById('theme-toggle');
        if (!toggleButton) return;
        
        const icon = toggleButton.querySelector('.theme-icon');
        if (icon) {
            if (theme === 'dark') {
                icon.textContent = '☀️'; // Sun for switching to light
            } else {
                icon.textContent = '🌙'; // Moon for switching to dark
            }
        }
    }
    
    /**
     * Toggle between dark and light theme
     */
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Save to localStorage
        localStorage.setItem(THEME_KEY, newTheme);
        
        // Apply the theme
        applyTheme(newTheme);
        
        // Show a brief notification
        if (typeof showNotification === 'function') {
            const message = newTheme === 'dark' ? 
                '🌙 Dark mode enabled' : 
                '☀️ Light mode enabled';
            showNotification(message, 'info');
        }
    }
    
    /**
     * Initialize theme on page load
     */
    let initialized = false;
    
    function initTheme() {
        if (initialized) return;  // Prevent double initialization
        initialized = true;
        
        const theme = getCurrentTheme();
        applyTheme(theme);
        
        // Set up the toggle button click handler
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', function(e) {
                e.preventDefault();
                toggleTheme();
            });
        }
        
        // Listen for system preference changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            // Only respond to system changes if user hasn't set a preference
            mediaQuery.addEventListener('change', function(e) {
                if (!localStorage.getItem(THEME_KEY)) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    applyTheme(newTheme);
                }
            });
        }
    }
    
    // Initialize theme as early as possible to avoid flash
    initTheme();
    
    // Also initialize on DOMContentLoaded in case script runs early
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    }
    
    // Expose theme functions globally for external use
    window.PlantedTheme = {
        toggle: toggleTheme,
        get: getCurrentTheme,
        set: function(theme) {
            localStorage.setItem(THEME_KEY, theme);
            applyTheme(theme);
        }
    };
})();
