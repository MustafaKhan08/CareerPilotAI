// User Profile Logic

const profileManager = {
    async init() {
        try {
            await this.loadUIComponents();
            this.bindEvents();
            await this.loadProfile();
        } catch (error) {
            console.error("Profile initialization failed:", error);
            utils.showNotification('Failed to initialize Profile module.', 'error');
        }
    },

    async loadUIComponents() {
        await Promise.all([
            new Promise(resolve => {
                utils.loadComponent('sidebar-container', '../components/sidebar.html', () => {
                    this.initSidebarLogic();
                    resolve();
                });
            }),
            new Promise(resolve => {
                utils.loadComponent('navbar-container', '../components/navbar.html', () => {
                    const nav = document.querySelector('nav');
                    if (nav) {
                        nav.classList.add('px-6', 'lg:px-10');
                        const toggleBtnHtml = `
                            <button type="button" class="md:hidden text-white mr-4 rounded focus-visible:ring-2 focus-visible:ring-primary" id="mobile-sidebar-toggle" aria-label="Open Sidebar">
                                <i class="fa-solid fa-bars text-xl"></i>
                            </button>
                        `;
                        const navBrand = nav.querySelector('.flex.items-center.gap-2');
                        if (navBrand) {
                            navBrand.insertAdjacentHTML('afterbegin', toggleBtnHtml);
                            const toggleBtn = document.getElementById('mobile-sidebar-toggle');
                            if(toggleBtn) toggleBtn.addEventListener('click', this.toggleSidebar.bind(this));
                        }
                    }
                    resolve();
                });
            })
        ]);
    },

    initSidebarLogic() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.sidebar-nav-item');
        navItems.forEach(item => {
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        const overlay = document.getElementById('sidebar-overlay');
        const closeBtn = document.getElementById('close-sidebar-btn');

        if (closeBtn) closeBtn.addEventListener('click', this.toggleSidebar.bind(this));
        if (overlay) overlay.addEventListener('click', this.toggleSidebar.bind(this));
    },

    toggleSidebar() {
        const sidebar = document.getElementById('app-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && overlay) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        }
    },

    bindEvents() {
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                router.logout();
            });
        }
    },

    escapeHTML(str) {
        if (str === null || str === undefined) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    setFieldValue(elementId, value, isStatus = false) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (value === null || value === undefined || value === '') {
            el.innerHTML = 'Not available';
            el.className = 'profile-field-value empty-state';
            return;
        }

        if (isStatus) {
            const isActive = value === true;
            el.innerHTML = `
                <span class="status-badge ${isActive ? 'active' : 'inactive'}">
                    <i class="fa-solid ${isActive ? 'fa-check' : 'fa-xmark'}"></i>
                    ${isActive ? 'Active' : 'Inactive'}
                </span>
            `;
            el.className = 'profile-field-value';
        } else {
            el.textContent = value;
            el.className = 'profile-field-value';
        }
    },

    getInitials(name) {
        if (!name) return '??';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    },

    async loadProfile() {
        const loadingState = document.getElementById('loading-state');
        const profileContent = document.getElementById('profile-content');
        
        try {
            // First, render cached data immediately for fast perceptual load
            const cachedUser = storage.getUser();
            if (cachedUser) {
                this.renderProfileData(cachedUser);
                loadingState.classList.add('hidden');
                profileContent.classList.remove('hidden');
            }

            // Fetch fresh data from backend (GET /users/me)
            const freshUser = await api.getCurrentUser();
            
            // Re-render and update cache
            this.renderProfileData(freshUser);
            storage.setUser(freshUser);
            
            // Hide loading state if there was no cached data initially
            if (!cachedUser) {
                loadingState.classList.add('hidden');
                profileContent.classList.remove('hidden');
            }
            
        } catch (error) {
            console.error("Error fetching user profile:", error);
            utils.showNotification(error.message || 'Failed to load profile data.', 'error');
            
            // If we have no cached data and the fetch failed, keep loading hidden and show a critical error
            if (!storage.getUser()) {
                loadingState.innerHTML = `
                    <i class="fa-solid fa-triangle-exclamation text-5xl text-red-500 mb-6"></i>
                    <h3 class="text-xl text-white font-medium mb-2">Failed to load profile</h3>
                    <p class="text-gray-400">Please try refreshing the page or logging in again.</p>
                `;
            } else if (error.message.toLowerCase().includes('unauthorized') || error.message.toLowerCase().includes('token')) {
                router.logout();
            }
        }
    },

    renderProfileData(user) {
        if (!user) return;

        // Header Avatar & Name
        const nameHeader = document.getElementById('profile-name-header');
        if (nameHeader) nameHeader.textContent = user.full_name || 'Unknown User';

        const avatar = document.getElementById('profile-avatar');
        if (avatar) avatar.textContent = this.getInitials(user.full_name);

        const roleBadge = document.getElementById('profile-role-badge');
        if (roleBadge && user.role) {
            roleBadge.textContent = user.role;
            roleBadge.classList.remove('hidden');
        }

        // Exact backend fields mapping (UserResponse schema)
        this.setFieldValue('val-full-name', user.full_name);
        this.setFieldValue('val-email', user.email);
        this.setFieldValue('val-role', user.role);
        
        this.setFieldValue('val-id', user.id ? `#${user.id}` : null);
        this.setFieldValue('val-status', user.is_active, true);
        
        this.setFieldValue('val-created', user.created_at ? utils.formatDate(user.created_at) : null);
        this.setFieldValue('val-updated', user.updated_at ? utils.formatDate(user.updated_at) : null);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    profileManager.init();
});
