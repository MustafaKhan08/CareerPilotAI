// Common Utilities

const utils = {
    /**
     * Dynamically loads an HTML component into a specified container.
     * @param {string} containerId - The ID of the container element.
     * @param {string} componentPath - The path to the HTML component file.
     * @param {Function} callback - Optional callback after the component is loaded.
     */
    async loadComponent(containerId, componentPath, callback) {
        try {
            const response = await fetch(componentPath);
            if (!response.ok) throw new Error(`Failed to load ${componentPath}`);
            const html = await response.text();
            
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = html;
                if (callback) callback();
            } else {
                console.warn(`Container ${containerId} not found.`);
            }
        } catch (error) {
            console.error('Error loading component:', error);
        }
    },

    /**
     * Shows a centralized toast notification.
     * @param {string} message - The message to display.
     * @param {string} type - 'success', 'error', 'info', 'warning'
     */
    showNotification(message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        
        // Define styles based on type
        const styles = {
            success: { bg: 'bg-green-500', icon: 'fa-check-circle' },
            error: { bg: 'bg-red-500', icon: 'fa-exclamation-circle' },
            warning: { bg: 'bg-yellow-500', icon: 'fa-exclamation-triangle' },
            info: { bg: 'bg-blue-500', icon: 'fa-info-circle' }
        };

        const currentStyle = styles[type] || styles.info;

        // Apply classes
        toast.className = `${currentStyle.bg} text-white px-5 py-3 rounded-lg shadow-lg flex items-center gap-3 transition-all duration-300 opacity-0 transform translate-x-8 pointer-events-auto`;
        
        // Accessibility semantics
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');

        toast.innerHTML = `
            <i class="fa-solid ${currentStyle.icon} text-lg"></i>
            <span class="font-medium">${message}</span>
        `;

        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('opacity-0', 'translate-x-8');
        });

        // Remove after 4 seconds
        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-x-8');
            setTimeout(() => {
                if (container.contains(toast)) {
                    container.removeChild(toast);
                }
            }, 300); // Wait for exit animation
        }, 4000);
    },

    /**
     * Formats an ISO date string to a readable format.
     */
    formatDate(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
};