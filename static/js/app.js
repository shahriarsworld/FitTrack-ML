
const FitTrackML = {
    // Show loading spinner on buttons
    showButtonLoading: function(button, loadingText = 'Loading...') {
        const originalText = button.innerHTML;
        button.dataset.originalText = originalText;
        button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
        button.disabled = true;
    },

    // Reset button from loading state
    resetButtonLoading: function(button) {
        const originalText = button.dataset.originalText;
        if (originalText) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastContainer = this.getToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const icon = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        }[type] || 'fas fa-info-circle';

        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `alert ${alertClass} alert-dismissible fade show toast-notification`;
        toast.innerHTML = `
            <i class="${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        toastContainer.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                toastElement.remove();
            }
        }, 5000);
    },

    // Get or create toast container
    getToastContainer: function() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1050;
                max-width: 350px;
            `;
            document.body.appendChild(container);
        }
        return container;
    },

    // Format numbers with proper decimals
    formatNumber: function(number, decimals = 1) {
        return parseFloat(number).toFixed(decimals);
    },

    // Calculate BMI
    calculateBMI: function(weight, height) {
        const heightInMeters = height / 100;
        return weight / (heightInMeters * heightInMeters);
    },

    // BMI Category
    getBMICategory: function(bmi) {
        if (bmi < 18.5) return { category: 'Underweight', color: 'text-info' };
        if (bmi < 25) return { category: 'Normal', color: 'text-success' };
        if (bmi < 30) return { category: 'Overweight', color: 'text-warning' };
        return { category: 'Obese', color: 'text-danger' };
    },

    // Animate counters
    animateCounter: function(element, targetValue, duration = 1000) {
        const startValue = 0;
        const increment = targetValue / (duration / 16);
        let currentValue = startValue;

        const updateCounter = () => {
            currentValue += increment;
            if (currentValue >= targetValue) {
                element.textContent = this.formatNumber(targetValue);
                return;
            }
            element.textContent = this.formatNumber(currentValue);
            requestAnimationFrame(updateCounter);
        };

        updateCounter();
    },

    // Local Storage helpers
    storage: {
        set: function(key, value) {
            try {
                localStorage.setItem(`fittrack_${key}`, JSON.stringify(value));
                return true;
            } catch (error) {
                console.error('Error saving to localStorage:', error);
                return false;
            }
        },

        get: function(key) {
            try {
                const item = localStorage.getItem(`fittrack_${key}`);
                return item ? JSON.parse(item) : null;
            } catch (error) {
                console.error('Error reading from localStorage:', error);
                return null;
            }
        },

        remove: function(key) {
            try {
                localStorage.removeItem(`fittrack_${key}`);
                return true;
            } catch (error) {
                console.error('Error removing from localStorage:', error);
                return false;
            }
        }
    },

    // API helpers
    api: {
        request: async function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            };

            const finalOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, finalOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                } else {
                    return await response.text();
                }
            } catch (error) {
                console.error('API request error:', error);
                throw error;
            }
        },

        get: function(url) {
            return this.request(url, { method: 'GET' });
        },

        post: function(url, data) {
            return this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        put: function(url, data) {
            return this.request(url, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        delete: function(url) {
            return this.request(url, { method: 'DELETE' });
        }
    }
};

// Form validation helpers
const FormValidation = {
    // Validate email format
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Validate password strength
    isValidPassword: function(password) {
        return password.length >= 6;
    },

    // Validate number range
    isValidNumber: function(value, min, max) {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    },

    // Add error message to form field
    showFieldError: function(fieldElement, message) {
        this.clearFieldError(fieldElement);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;
        
        fieldElement.classList.add('is-invalid');
        fieldElement.parentNode.appendChild(errorDiv);
    },

    // Clear error message from form field
    clearFieldError: function(fieldElement) {
        fieldElement.classList.remove('is-invalid');
        const errorDiv = fieldElement.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    },

    // Validate entire form
    validateForm: function(formElement) {
        const inputs = formElement.querySelectorAll('input[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            this.clearFieldError(input);
            
            if (!input.value.trim()) {
                this.showFieldError(input, 'This field is required');
                isValid = false;
            } else if (input.type === 'email' && !this.isValidEmail(input.value)) {
                this.showFieldError(input, 'Please enter a valid email address');
                isValid = false;
            } else if (input.type === 'password' && !this.isValidPassword(input.value)) {
                this.showFieldError(input, 'Password must be at least 6 characters long');
                isValid = false;
            } else if (input.type === 'number') {
                const min = parseFloat(input.getAttribute('min'));
                const max = parseFloat(input.getAttribute('max'));
                if (!this.isValidNumber(input.value, min, max)) {
                    this.showFieldError(input, `Please enter a value between ${min} and ${max}`);
                    isValid = false;
                }
            }
        });

        return isValid;
    }
};

// Chart helpers - UPDATED VERSION
const ChartHelpers = {
    // Default chart options
    getDefaultOptions: function() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#666',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    },
                    beginAtZero: false
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };
    },

    // Color schemes
    getColorScheme: function(type = 'primary') {
        const schemes = {
            primary: {
                background: 'rgba(102, 126, 234, 0.2)',
                border: 'rgb(102, 126, 234)'
            },
            success: {
                background: 'rgba(72, 187, 120, 0.2)',
                border: 'rgb(72, 187, 120)'
            },
            warning: {
                background: 'rgba(237, 137, 54, 0.2)',
                border: 'rgb(237, 137, 54)'
            },
            info: {
                background: 'rgba(66, 153, 225, 0.2)',
                border: 'rgb(66, 153, 225)'
            },
            weight: {
                background: 'rgba(75, 192, 192, 0.2)',
                border: 'rgb(75, 192, 192)'
            }
        };
        return schemes[type] || schemes.primary;
    },

    // Create line chart for progress tracking
    createProgressChart: function(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas with id '${canvasId}' not found`);
            return null;
        }

        const ctx = canvas.getContext('2d');
        const defaultOptions = this.getDefaultOptions();
        const finalOptions = { ...defaultOptions, ...options };

        return new Chart(ctx, {
            type: 'line',
            data: data,
            options: finalOptions
        });
    },

    // Destroy chart safely
    destroyChart: function(chartInstance) {
        if (chartInstance && typeof chartInstance.destroy === 'function') {
            chartInstance.destroy();
        }
    },

    // Format chart data for progress tracking
    formatProgressData: function(dates, weights, label = 'Weight (kg)') {
        const colors = this.getColorScheme('weight');
        
        return {
            labels: dates,
            datasets: [{
                label: label,
                data: weights,
                borderColor: colors.border,
                backgroundColor: colors.background,
                tension: 0.1,
                fill: true,
                borderWidth: 2,
                pointBackgroundColor: colors.border,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        };
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Add smooth scrolling for anchor links
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

    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    });
});

// Export for global use
window.FitTrackML = FitTrackML;
window.FormValidation = FormValidation;
window.ChartHelpers = ChartHelpers;
