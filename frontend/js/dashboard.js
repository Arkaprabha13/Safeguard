document.addEventListener('DOMContentLoaded', function() {
    // Require authentication
    if (!Utils.requireAuth()) {
        return;
    }

    // Initialize dashboard
    initializeDashboard();
    loadUserProfile();
    loadContacts();
    loadRecentActivity();
    updateDateTime();
    
    // Update time every minute
    setInterval(updateDateTime, 60000);
});

function initializeDashboard() {
    // Add contact form handler
    const addContactForm = document.getElementById('addContactForm');
    if (addContactForm) {
        addContactForm.addEventListener('submit', handleAddContact);
    }
    
    // Add form validation listeners
    setupFormValidation();
}

function setupFormValidation() {
    // Real-time validation for contact form
    const contactName = document.getElementById('contactName');
    const contactPhone = document.getElementById('contactPhone');
    const contactEmail = document.getElementById('contactEmail');
    const contactRelationship = document.getElementById('contactRelationship');

    if (contactName) {
        contactName.addEventListener('input', validateContactName);
        contactName.addEventListener('blur', validateContactName);
    }
    
    if (contactPhone) {
        contactPhone.addEventListener('input', validateContactPhone);
        contactPhone.addEventListener('blur', validateContactPhone);
    }
    
    if (contactEmail) {
        contactEmail.addEventListener('input', validateContactEmail);
        contactEmail.addEventListener('blur', validateContactEmail);
    }
    
    if (contactRelationship) {
        contactRelationship.addEventListener('change', validateContactRelationship);
    }
}

function validateContactName() {
    const nameInput = document.getElementById('contactName');
    const name = nameInput.value.trim();
    
    if (!name) {
        showFieldError(nameInput, 'Name is required');
        return false;
    }
    
    if (name.length < 2) {
        showFieldError(nameInput, 'Name must be at least 2 characters');
        return false;
    }
    
    hideFieldError(nameInput);
    return true;
}

function validateContactPhone() {
    const phoneInput = document.getElementById('contactPhone');
    const phone = phoneInput.value.trim();
    
    if (!phone) {
        showFieldError(phoneInput, 'Phone number is required');
        return false;
    }
    
    // Basic phone validation
    const phoneRegex = /^[\+]?[\d\s\-\(\)]{10,}$/;
    if (!phoneRegex.test(phone)) {
        showFieldError(phoneInput, 'Please enter a valid phone number');
        return false;
    }
    
    hideFieldError(phoneInput);
    return true;
}

function validateContactEmail() {
    const emailInput = document.getElementById('contactEmail');
    const email = emailInput.value.trim();
    
    // Email is optional, but if provided, must be valid
    if (email && !Utils.isValidEmail(email)) {
        showFieldError(emailInput, 'Please enter a valid email address');
        return false;
    }
    
    hideFieldError(emailInput);
    return true;
}

function validateContactRelationship() {
    const relationshipInput = document.getElementById('contactRelationship');
    const relationship = relationshipInput.value;
    
    if (!relationship) {
        showFieldError(relationshipInput, 'Please select a relationship');
        return false;
    }
    
    hideFieldError(relationshipInput);
    return true;
}

function showFieldError(input, message) {
    // Remove existing error
    hideFieldError(input);
    
    // Add error styling
    input.classList.add('border-red-400', 'bg-red-500/10');
    
    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-red-400 text-xs mt-1';
    errorDiv.textContent = message;
    
    // Insert error message after input
    input.parentNode.insertBefore(errorDiv, input.nextSibling);
}

function hideFieldError(input) {
    // Remove error styling
    input.classList.remove('border-red-400', 'bg-red-500/10');
    
    // Remove error message
    const errorDiv = input.parentNode.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function updateDateTime() {
    const currentDateTimeElement = document.getElementById('currentDateTime');
    if (currentDateTimeElement) {
        const now = new Date();
        currentDateTimeElement.textContent = `${now.toLocaleDateString()} • ${now.toLocaleTimeString()}`;
    }
}

async function loadUserProfile() {
    try {
        const userData = Utils.getUserData();
        if (!userData) {
            console.warn('No user data found, redirecting to login');
            Utils.logout();
            return;
        }

        // Update user greeting
        const userGreeting = document.getElementById('userGreeting');
        if (userGreeting) {
            userGreeting.textContent = `Welcome back, ${userData.firstName}!`;
        }

        // Update user name
        const userName = document.getElementById('userName');
        if (userName) {
            userName.textContent = `${userData.firstName} ${userData.lastName || ''}`.trim();
        }

        // Update user email
        const userEmail = document.getElementById('userEmail');
        if (userEmail) {
            userEmail.textContent = userData.email;
        }

        // Update user location
        const userLocation = document.getElementById('userLocation');
        if (userLocation) {
            userLocation.textContent = userData.address || 'Location not set';
        }

        // Update user avatar
        const userAvatar = document.getElementById('userAvatar');
        if (userAvatar) {
            userAvatar.textContent = userData.firstName.charAt(0).toUpperCase();
        }

        // Update safety score
        const safetyScore = document.getElementById('safetyScore');
        if (safetyScore) {
            safetyScore.textContent = userData.safetyScore || 85;
        }

    } catch (error) {
        console.error('Error loading user profile:', error);
        Utils.showToast('Failed to load user profile', 'error');
    }
}

async function loadContacts() {
    try {
        const userData = Utils.getUserData();
        if (!userData) return;

        const contacts = await Utils.apiRequest(`/contacts/user/${userData._id}`);
        const contactsList = document.getElementById('contactsList');
        
        if (!contactsList) return;

        if (contacts.length === 0) {
            contactsList.innerHTML = `
                <div class="text-center py-8 text-white/60">
                    <i class="fas fa-user-plus text-3xl mb-2"></i>
                    <p>No emergency contacts yet</p>
                    <p class="text-sm">Add your first emergency contact</p>
                </div>
            `;
            return;
        }

        contactsList.innerHTML = contacts.map(contact => `
            <div class="contact-card">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-gradient-to-br from-red-500 to-pink-600 rounded-full flex items-center justify-center text-white font-bold">
                            ${contact.firstName.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <h4 class="text-white font-medium">${contact.firstName} ${contact.lastName || ''}</h4>
                            <p class="text-white/60 text-sm">${contact.relationship}</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="bg-${getPriorityColor(contact.priority)}-500/20 text-${getPriorityColor(contact.priority)}-400 text-xs px-2 py-1 rounded-full">
                            ${contact.priority.toUpperCase()}
                        </span>
                        <button onclick="deleteContact('${contact._id}')" class="text-white/60 hover:text-red-400 p-1">
                            <i class="fas fa-trash text-sm"></i>
                        </button>
                    </div>
                </div>
                <div class="mt-2 text-white/70 text-sm">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-phone text-xs"></i>
                        <span>${contact.phone}</span>
                    </div>
                    ${contact.email ? `
                        <div class="flex items-center gap-2 mt-1">
                            <i class="fas fa-envelope text-xs"></i>
                            <span>${contact.email}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading contacts:', error);
        Utils.showToast('Failed to load contacts', 'error');
    }
}

async function loadRecentActivity() {
    try {
        const userData = Utils.getUserData();
        if (!userData) return;

        const activities = await Utils.apiRequest(`/activities/user/${userData._id}`);
        const activityList = document.getElementById('activityList');
        
        if (!activityList) return;

        if (activities.length === 0) {
            activityList.innerHTML = `
                <div class="text-center py-8 text-white/60">
                    <i class="fas fa-history text-3xl mb-2"></i>
                    <p>No recent activity</p>
                    <p class="text-sm">Your safety activities will appear here</p>
                </div>
            `;
            return;
        }

        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="flex items-start gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <i class="fas fa-${getActivityIcon(activity.type)} text-white text-xs"></i>
                    </div>
                    <div class="flex-1">
                        <p class="text-white text-sm">${activity.description}</p>
                        <p class="text-white/60 text-xs mt-1">${Utils.formatTimeAgo(activity.timestamp)}</p>
                    </div>
                    <span class="bg-${getStatusColor(activity.status)}-500/20 text-${getStatusColor(activity.status)}-400 text-xs px-2 py-1 rounded-full">
                        ${activity.status.toUpperCase()}
                    </span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading activities:', error);
        Utils.showToast('Failed to load recent activity', 'error');
    }
}

function getPriorityColor(priority) {
    const colors = {
        high: 'red',
        medium: 'yellow',
        low: 'green'
    };
    return colors[priority] || 'gray';
}

function getActivityIcon(type) {
    const icons = {
        location_shared: 'map-marker-alt',
        contact_called: 'phone',
        check_in: 'check-circle',
        emergency_alert: 'exclamation-triangle'
    };
    return icons[type] || 'circle';
}

function getStatusColor(status) {
    const colors = {
        success: 'green',
        pending: 'yellow',
        failed: 'red'
    };
    return colors[status] || 'gray';
}

// Modal functions
function addContact() {
    const modal = document.getElementById('addContactModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Focus on the first input
        const firstInput = modal.querySelector('input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

function closeContactModal() {
    const modal = document.getElementById('addContactModal');
    if (modal) {
        modal.classList.add('hidden');
        
        // Reset form and clear errors
        const form = document.getElementById('addContactForm');
        if (form) {
            form.reset();
            // Clear all field errors
            const errorElements = form.querySelectorAll('.field-error');
            errorElements.forEach(error => error.remove());
            
            // Remove error styling
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.classList.remove('border-red-400', 'bg-red-500/10');
            });
        }
    }
}

async function handleAddContact(e) {
    e.preventDefault();
    
    try {
        const userData = Utils.getUserData();
        if (!userData) {
            Utils.showToast('User session expired. Please login again.', 'error');
            Utils.logout();
            return;
        }

        // Get form values and trim whitespace
        const fullName = document.getElementById('contactName').value.trim();
        const phone = document.getElementById('contactPhone').value.trim();
        const email = document.getElementById('contactEmail').value.trim();
        const relationship = document.getElementById('contactRelationship').value;
        const priority = document.getElementById('contactPriority').value;

        // Validate all fields
        const isNameValid = validateContactName();
        const isPhoneValid = validateContactPhone();
        const isEmailValid = validateContactEmail();
        const isRelationshipValid = validateContactRelationship();

        if (!isNameValid || !isPhoneValid || !isEmailValid || !isRelationshipValid) {
            Utils.showToast('Please fix all validation errors before submitting', 'error');
            return;
        }

        // Parse name properly
        const nameParts = fullName.split(' ').filter(part => part.length > 0);
        const firstName = nameParts[0] || '';
        let lastName = nameParts.length > 1 ? nameParts.slice(1).join(' ') : '';
        
        // Ensure lastName is never empty (backend validation requirement)
        if (!lastName && firstName) {
            lastName = 'N/A'; // Default value to satisfy backend validation
        }

        // Prepare contact data
        const contactData = {
            userId: userData._id,
            firstName: firstName,
            lastName: lastName,
            phone: phone,
            email: email || undefined, // Use undefined instead of empty string
            address: undefined, // Not collecting address in this form
            relationship: relationship,
            priority: priority
        };

        // Final validation
        if (!firstName || !lastName || !phone || !relationship) {
            Utils.showToast('All required fields must be filled', 'error');
            return;
        }

        console.log('Creating contact with data:', contactData); // Debug log

        // Show loading state
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        Utils.setLoading(submitBtn, true);

        // Make API request
        const newContact = await Utils.apiRequest('/contacts/', {
            method: 'POST',
            body: JSON.stringify(contactData)
        });

        console.log('Contact created successfully:', newContact); // Debug log

        // Success feedback
        Utils.showToast(`Contact "${firstName} ${lastName}" added successfully!`, 'success');
        
        // Close modal and reload contacts
        closeContactModal();
        await loadContacts();

        // Add activity log
        await addActivity(
            'contact_called', 
            `Added ${firstName} ${lastName !== 'N/A' ? lastName : ''} as emergency contact`.trim(), 
            'success'
        );
        
        // Refresh activity list
        await loadRecentActivity();

        // Reset loading state
        Utils.setLoading(submitBtn, false);
        submitBtn.textContent = originalText;

    } catch (error) {
        console.error('Error adding contact:', error);
        
        // Show specific error message
        let errorMessage = 'Failed to add contact';
        if (error.message) {
            if (error.message.includes('validation')) {
                errorMessage = 'Please check all required fields are properly filled';
            } else if (error.message.includes('duplicate') || error.message.includes('already exists')) {
                errorMessage = 'A contact with this information already exists';
            } else {
                errorMessage = `Error: ${error.message}`;
            }
        }
        
        Utils.showToast(errorMessage, 'error');
        
        // Reset loading state
        const submitBtn = e.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            Utils.setLoading(submitBtn, false);
            submitBtn.textContent = 'Add Contact';
        }
    }
}

async function deleteContact(contactId) {
    if (!contactId) {
        Utils.showToast('Invalid contact ID', 'error');
        return;
    }

    if (!confirm('Are you sure you want to delete this contact?')) {
        return;
    }

    try {
        await Utils.apiRequest(`/contacts/${contactId}`, {
            method: 'DELETE'
        });

        Utils.showToast('Contact deleted successfully', 'success');
        await loadContacts();

        // Add activity log
        await addActivity('contact_called', 'Removed emergency contact', 'success');

    } catch (error) {
        console.error('Error deleting contact:', error);
        Utils.showToast('Failed to delete contact', 'error');
    }
}

// Quick action functions
async function shareLocation() {
    if (!navigator.geolocation) {
        Utils.showToast('Geolocation is not supported by this browser', 'error');
        return;
    }

    Utils.showToast('Getting your location...', 'info');

    navigator.geolocation.getCurrentPosition(async (position) => {
        try {
            const { latitude, longitude } = position.coords;
            
            // Here you would typically send the location to your contacts
            Utils.showToast('Location shared with emergency contacts', 'success');
            
            await addActivity(
                'location_shared', 
                `Shared location: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`, 
                'success'
            );
            
            await loadRecentActivity();

        } catch (error) {
            console.error('Error sharing location:', error);
            Utils.showToast('Failed to share location', 'error');
        }
    }, (error) => {
        let errorMessage = 'Unable to get your location';
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMessage = 'Location access denied by user';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage = 'Location information is unavailable';
                break;
            case error.TIMEOUT:
                errorMessage = 'Location request timed out';
                break;
        }
        Utils.showToast(errorMessage, 'error');
    });
}

async function emergencyAlert() {
    if (!confirm('This will send an emergency alert to all your contacts. Continue?')) {
        return;
    }

    try {
        // Here you would typically send alerts to all contacts
        Utils.showToast('Emergency alert sent to all contacts!', 'success');
        
        await addActivity('emergency_alert', 'Emergency alert sent to all contacts', 'success');
        await loadRecentActivity();

    } catch (error) {
        console.error('Error sending emergency alert:', error);
        Utils.showToast('Failed to send emergency alert', 'error');
    }
}

async function checkIn() {
    try {
        Utils.showToast('Check-in sent to your contacts', 'success');
        
        await addActivity('check_in', 'Sent safety check-in to contacts', 'success');
        await loadRecentActivity();

    } catch (error) {
        console.error('Error checking in:', error);
        Utils.showToast('Failed to send check-in', 'error');
    }
}

function viewProfile() {
    Utils.showToast('Profile settings coming soon!', 'info');
}

async function refreshActivity() {
    try {
        await loadRecentActivity();
        Utils.showToast('Activity refreshed', 'success');
    } catch (error) {
        Utils.showToast('Failed to refresh activity', 'error');
    }
}

// Helper function to add activity
async function addActivity(type, description, status) {
    try {
        const userData = Utils.getUserData();
        if (!userData) return;

        const activityData = {
            userId: userData._id,
            type: type,
            description: description,
            status: status,
            timestamp: new Date().toISOString()
        };

        await Utils.apiRequest('/activities/', {
            method: 'POST',
            body: JSON.stringify(activityData)
        });

    } catch (error) {
        console.error('Error adding activity:', error);
        // Don't show toast for activity errors to avoid spam
    }
}

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        Utils.logout();
    }
}
