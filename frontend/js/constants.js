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
    },
};

Object.freeze(CONSTANTS);