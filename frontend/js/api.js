// Centralized API Client

const api = {
    /**
     * Base fetch wrapper that handles authorization and JSON parsing.
     */
    async fetchJSON(endpoint, options = {}) {
        const url = `${config.API_BASE_URL}${endpoint}`;
        
        const headers = {
            ...CONSTANTS.DEFAULT_HEADERS,
            ...(options.headers || {})
        };

        const token = storage.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const configOptions = {
            ...options,
            headers
        };

        // For FormData, let the browser set the Content-Type
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        const response = await fetch(url, configOptions);
        
        if (!response.ok) {
            let errorMsg = 'An error occurred';
            try {
                const errData = await response.json();
                errorMsg = errData.detail || errorMsg;
            } catch (e) {
                errorMsg = response.statusText;
            }
            throw new Error(errorMsg);
        }

        // If response is 204 No Content, return null
        if (response.status === 204) {
            return null;
        }
        
        // For PDF downloads, return the blob instead of json
        if (response.headers.get('Content-Type') === 'application/pdf') {
            return await response.blob();
        }

        return await response.json();
    },

    // ==========================================
    // USERS
    // ==========================================
    async register(userData) {
        return this.fetchJSON(CONSTANTS.ENDPOINTS.REGISTER, {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    async login(credentials) {
        return this.fetchJSON(CONSTANTS.ENDPOINTS.LOGIN, {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
    },

    async getCurrentUser() {
        return this.fetchJSON(CONSTANTS.ENDPOINTS.ME);
    },

    // ==========================================
    // RESUMES
    // ==========================================
    async uploadResume(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.RESUMES}/upload`, {
            method: 'POST',
            body: formData
        });
    },

    async listResumes() {
        return this.fetchJSON(CONSTANTS.ENDPOINTS.RESUMES);
    },

    async getResume(id) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.RESUMES}/${id}`);
    },

    async deleteResume(id) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.RESUMES}/${id}`, {
            method: 'DELETE'
        });
    },

    // ==========================================
    // AI
    // ==========================================
  async analyzeResume(id, regenerate = false) {
        return this.fetchJSON(
            `${CONSTANTS.ENDPOINTS.AI_RESUMES}/${id}/analyze?regenerate=${regenerate}`,
            {
                method: 'POST'
            }
        );
    },

    // ==========================================
    // ANALYSES
    // ==========================================
    async getResumeAnalyses(resumeId) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.ANALYSES}/resumes/${resumeId}`);
    },

    async getLatestAnalysis(resumeId) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.ANALYSES}/resumes/${resumeId}/latest`);
    },

    async deleteResumeAnalysis(resumeId) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.ANALYSES}/resumes/${resumeId}`, {
            method: 'DELETE'
        });
    },

    async getAnalysis(id) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.ANALYSES}/${id}`);
    },

    async deleteAnalysis(id) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.ANALYSES}/${id}`, {
            method: 'DELETE'
        });
    },

    // ==========================================
    // JOBS
    // ==========================================
    async listJobs(page = 1, limit = 20) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.JOBS}?page=${page}&limit=${limit}`);
    },

    async createJob(jobData) {
        return this.fetchJSON(CONSTANTS.ENDPOINTS.JOBS, {
            method: 'POST',
            body: JSON.stringify(jobData)
        });
    },

    async searchJobs(queryParams) {
        const params = new URLSearchParams(queryParams).toString();
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.JOBS}/search?${params}`);
    },

    async getJob(id) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.JOBS}/${id}`);
    },

    async deleteJob(id) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.JOBS}/${id}`, {
            method: 'DELETE'
        });
    },

    async importJobs(data) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.JOBS}/import`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // ==========================================
    // AI CAREER MENTOR
    // ==========================================
    async sendChatMessage(message) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.CHAT}/message`, {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    },

    async getChatHistory() {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.CHAT}/history`);
    },

    async deleteChatHistory() {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.CHAT}/history`, {
            method: 'DELETE'
        });
    },

    // ==========================================
    // INTERVIEWS
    // ==========================================
    async startInterview(data) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.INTERVIEWS}/start`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async submitInterviewAnswer(sessionId, answer) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.INTERVIEWS}/${sessionId}/answer`, {
            method: 'POST',
            body: JSON.stringify({ answer })
        });
    },

    async getInterviewReport(sessionId) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.INTERVIEWS}/${sessionId}/report`);
    },

    async downloadInterviewPDF(sessionId) {
        return this.fetchJSON(`${CONSTANTS.ENDPOINTS.INTERVIEWS}/${sessionId}/report/pdf`);
    }
};
