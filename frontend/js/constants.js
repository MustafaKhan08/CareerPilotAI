// =======================================================
// CareerPilotAI - Application Constants
// =======================================================

const CONSTANTS = {

    // ---------------------------------------------------
    // Local Storage Keys
    // ---------------------------------------------------
    STORAGE_KEYS: {
        TOKEN: "career_pilot_jwt",
        USER: "career_pilot_user",
    },

    // ---------------------------------------------------
    // Default Request Headers
    // ---------------------------------------------------
    DEFAULT_HEADERS: {
        "Content-Type": "application/json",
    },

    // ---------------------------------------------------
    // API Endpoints
    // ---------------------------------------------------
    ENDPOINTS: {

        // Authentication
        LOGIN: "/users/login",
        REGISTER: "/users/register",
        ME: "/users/me",

        // Email verification
        VERIFY_EMAIL: "/users/verify-email",
        RESEND_VERIFICATION: "/users/resend-verification",

        // Password reset
        FORGOT_PASSWORD: "/users/forgot-password",
        RESET_PASSWORD: "/users/reset-password",

        // Resume
        RESUMES: "/resumes",

        // Resume Analysis
        ANALYSES: "/analyses",

        // AI
        AI_RESUMES: "/ai/resumes",

        // Jobs
        JOBS: "/jobs",

        // Chat
        CHAT: "/chat",

        // Interviews
        INTERVIEWS: "/interviews",
    },

    // ---------------------------------------------------
    // Frontend Routes
    // ---------------------------------------------------
    ROUTES: {
        HOME: "/",
        LOGIN: "/pages/login.html",
        REGISTER: "/pages/register.html",
        DASHBOARD: "/pages/dashboard.html",
        RESUME: "/pages/resume.html",
        JOBS: "/pages/jobs.html",
        MENTOR: "/pages/mentor.html",
        INTERVIEW: "/pages/interview.html",
        PROFILE: "/pages/profile.html",
        FORGOT_PASSWORD: "/pages/forgot-password.html",
        RESET_PASSWORD: "/pages/reset-password.html",
        VERIFY_EMAIL: "/pages/verify-email.html",
    },
};

Object.freeze(CONSTANTS);
