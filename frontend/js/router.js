// Routing and Navigation

const router = {
    /**
     * Initializes the router and checks access rights based on the current path.
     */
    init() {
        this.checkAuth();
    },

    /**
     * Checks if the user is authorized to view the current page.
     * Handles redirects for protected and public routes.
     */
    checkAuth() {
        const path = window.location.pathname;
        const isAuth = storage.isAuthenticated();
        
        // Public routes that authenticated users shouldn't see (e.g., login, register)
        const publicOnlyRoutes = [
            CONSTANTS.ROUTES.LOGIN,
            CONSTANTS.ROUTES.REGISTER,
            CONSTANTS.ROUTES.HOME,
            '/index.html'
        ];

        // If authenticated and trying to access a public-only page, redirect
        if (isAuth && publicOnlyRoutes.includes(path)) {
            // Check if there's a specific redirect requested
            const urlParams = new URLSearchParams(window.location.search);
            const redirectUrl = urlParams.get('redirect');
            this.navigate(redirectUrl || CONSTANTS.ROUTES.DASHBOARD);
            return;
        }

        // If not authenticated and trying to access a protected page, redirect to login
        if (!isAuth && !publicOnlyRoutes.includes(path)) {
            // Check if we are really on a page and not just at the root '/'
            if (path !== CONSTANTS.ROUTES.HOME && path !== '/index.html' && path !== '/') {
                // Save the requested URL to redirect back after login
                const redirectParam = encodeURIComponent(path + window.location.search);
                this.navigate(`${CONSTANTS.ROUTES.LOGIN}?redirect=${redirectParam}`);
            }
        }
    },

    /**
     * Navigates to a specific route.
     * @param {string} route - The target route URL
     */
    navigate(route) {
        window.location.href = route;
    },

    /**
     * Logs the user out and redirects to login.
     */
    logout() {
        storage.clearAll();
        this.navigate(CONSTANTS.ROUTES.LOGIN);
    }
};

// Run auth check automatically when script loads
document.addEventListener("DOMContentLoaded", () => {
    router.init();
});