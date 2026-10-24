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

        // Routes only unauthenticated users should see (login, register).
        // Authenticated users hitting these are bounced to the dashboard.
        const publicOnlyRoutes = [
            CONSTANTS.ROUTES.LOGIN,
            CONSTANTS.ROUTES.REGISTER,
            CONSTANTS.ROUTES.HOME,
            '/index.html'
        ];

        // Routes that are always public — never redirect unauthenticated visitors.
        // Email-flow pages must be accessible without a JWT.
        const alwaysPublicRoutes = [
            ...publicOnlyRoutes,
            CONSTANTS.ROUTES.FORGOT_PASSWORD,
            CONSTANTS.ROUTES.RESET_PASSWORD,
            CONSTANTS.ROUTES.VERIFY_EMAIL,
        ];

        // If authenticated and trying to access a public-only page, redirect to dashboard.
        if (isAuth && publicOnlyRoutes.includes(path)) {
            const urlParams = new URLSearchParams(window.location.search);
            const redirectUrl = urlParams.get('redirect');
            this.navigate(redirectUrl || CONSTANTS.ROUTES.DASHBOARD);
            return;
        }

        // If not authenticated and trying to access a protected page, redirect to login.
        if (!isAuth && !alwaysPublicRoutes.includes(path)) {
            if (path !== CONSTANTS.ROUTES.HOME && path !== '/index.html' && path !== '/') {
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
