// =======================================================
// CareerPilotAI - Local Storage Utilities
// =======================================================

const storage = {

    // ---------------------------------------------------
    // JWT Token
    // ---------------------------------------------------

    setToken(token) {
        localStorage.setItem(CONSTANTS.STORAGE_KEYS.TOKEN, token);
    },

    getToken() {
        return localStorage.getItem(CONSTANTS.STORAGE_KEYS.TOKEN);
    },

    removeToken() {
        localStorage.removeItem(CONSTANTS.STORAGE_KEYS.TOKEN);
    },

    hasToken() {
        return !!this.getToken();
    },

    isAuthenticated() {
        return this.hasToken();
    },

    // ---------------------------------------------------
    // User Information
    // ---------------------------------------------------

    setUser(user) {
        localStorage.setItem(
            CONSTANTS.STORAGE_KEYS.USER,
            JSON.stringify(user)
        );
    },

    getUser() {
        const user = localStorage.getItem(CONSTANTS.STORAGE_KEYS.USER);

        if (!user) return null;

        try {
            return JSON.parse(user);
        } catch (error) {
            console.error("Failed to parse stored user data:", error);

            this.removeUser();

            return null;
        }
    },

    removeUser() {
        localStorage.removeItem(CONSTANTS.STORAGE_KEYS.USER);
    },

    // ---------------------------------------------------
    // Clear Everything (Logout)
    // ---------------------------------------------------

    clearAll() {
        this.removeToken();
        this.removeUser();
    }
};