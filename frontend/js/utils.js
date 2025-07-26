// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Utility Functions
class Utils {
    // Show toast notification
    static showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="${icons[type]} text-lg"></i>
                <span>${message}</span>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (container.contains(toast)) {
                    container.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    // Make API request
    static async apiRequest(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Validate email format
    static isValidEmail(email) {
        return /\S+@\S+\.\S+/.test(email);
    }

    // Validate phone format
    static isValidPhone(phone) {
        return /^\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}$/.test(phone);
    }

    // Format time ago
    static formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInSeconds = Math.floor((now - time) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
        
        return time.toLocaleDateString();
    }

    // Get user data from localStorage
    static getUserData() {
        const userData = localStorage.getItem('userData');
        return userData ? JSON.parse(userData) : null;
    }

    // Save user data to localStorage
    static saveUserData(userData) {
        localStorage.setItem('userData', JSON.stringify(userData));
        localStorage.setItem('userEmail', userData.email);
        localStorage.setItem('userId', userData._id);
        localStorage.setItem('isAuthenticated', 'true');
    }

    // Check if user is authenticated
    static isAuthenticated() {
        return localStorage.getItem('isAuthenticated') === 'true';
    }

    // Logout user
    static logout() {
        localStorage.removeItem('userData');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userId');
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('authToken');
        window.location.href = 'index.html';
    }

    // Redirect if not authenticated
    static requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'index.html';
            return false;
        }
        return true;
    }

    // Show/hide loading state
    static setLoading(element, isLoading, originalText = '') {
        const textElement = element.querySelector('span') || element;
        const spinner = element.querySelector('.fa-spinner');
        
        if (isLoading) {
            element.disabled = true;
            if (spinner) spinner.classList.remove('hidden');
            if (originalText) textElement.textContent = 'Loading...';
        } else {
            element.disabled = false;
            if (spinner) spinner.classList.add('hidden');
            if (originalText) textElement.textContent = originalText;
        }
    }
}

// Export for use in other files
window.Utils = Utils;
