// AI Resume Analysis Module Logic

const analysisManager = {
    isRegenerate: false,
    selectedResumeId: null,
    resumes: [],
    currentDeleteId: null,
    lastFocusedElement: null,

    async init() {
        try {
            await this.loadUIComponents();
            this.bindEvents();
            await this.loadResumes();
            this.checkForInitialResume();
        } catch (error) {
            console.error("Initialization failed:", error);
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
        // Resume Selector
        const selector = document.getElementById('resume-selector');
        if (selector) {
            selector.addEventListener('change', (e) => {
                this.selectResume(e.target.value);
            });
        }

        // Analyze Button
        const analyzeBtn = document.getElementById('start-analysis-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', this.startAnalysis.bind(this));
        }

        // History container event delegation
        const historyContainer = document.getElementById('history-container');
        if (historyContainer) {
            historyContainer.addEventListener('click', (e) => {
                const actionBtn = e.target.closest('.action-btn');
                if (!actionBtn) return;
                
                const action = actionBtn.getAttribute('data-action');
                const id = actionBtn.getAttribute('data-id');
                
                if (action === 'view') {
                    this.openDetailsModal(id);
                } else if (action === 'delete') {
                    this.openDeleteModal(id);
                }
            });
        }

        // Modals closing
        document.querySelectorAll('.modal-close, .modal-cancel, .modal-close-internal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal-overlay');
                if (modal) this.closeModal(modal.id);
            });
        });

        // Delete Confirmations
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', this.handleDelete.bind(this));
        }

        const confirmDeleteAllBtn = document.getElementById('confirm-delete-all-btn');
        if (confirmDeleteAllBtn) {
            confirmDeleteAllBtn.addEventListener('click', this.handleDeleteAllHistory.bind(this));
        }
        
        const deleteAllHistoryBtn = document.getElementById('delete-all-history-btn');
        if (deleteAllHistoryBtn) {
            deleteAllHistoryBtn.addEventListener('click', () => {
                if (this.selectedResumeId) {
                    this.openModal('delete-all-modal');
                }
            });
        }

        // Accessibility: Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                    this.closeModal(modal.id);
                });
            }
        });
    },

    escapeHTML(str) {
        if (!str && str !== 0) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    async loadResumes() {
        try {
            const selector = document.getElementById('resume-selector');
            selector.innerHTML = '<option value="" disabled selected>Loading resumes...</option>';
            
            this.resumes = await api.listResumes();
            
            if (!this.resumes || this.resumes.length === 0) {
                selector.innerHTML = '<option value="" disabled selected>No resumes found. Upload one first.</option>';
                return;
            }

            // Sort newest first without mutating original array
            const sortedResumes = [...this.resumes].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

            selector.innerHTML = '<option value="" disabled selected>Select a resume to analyze...</option>';
            sortedResumes.forEach(resume => {
                const option = document.createElement('option');
                option.value = resume.id;
                option.textContent = resume.original_filename || 'Untitled';
                selector.appendChild(option);
            });

        } catch (error) {
            console.error(error);
            const selector = document.getElementById('resume-selector');
            selector.innerHTML = '<option value="" disabled selected>Failed to load resumes</option>';
            utils.showNotification('Failed to load your resumes.', 'error');
        }
    },

    checkForInitialResume() {
        const urlParams = new URLSearchParams(window.location.search);
        const resumeId = urlParams.get('resume_id');
        
        if (resumeId) {
            const selector = document.getElementById('resume-selector');
            
            // Check if this ID exists in our loaded resumes
            const exists = this.resumes.some(r => String(r.id) === String(resumeId));
            if (exists) {
                selector.value = resumeId;
                this.selectResume(resumeId);
            } else {
                utils.showNotification('Selected resume not found. It may have been deleted.', 'warning');
                // Clean URL
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        }
    },

    selectResume(resumeId) {
        this.selectedResumeId = resumeId;
        const resume = this.resumes.find(r => String(r.id) === String(resumeId));
        
        if (!resume) return;

        // Update URL to allow sharing/refreshing (use replaceState to avoid history bloat)
        const url = new URL(window.location);
        url.searchParams.set('resume_id', resumeId);
        window.history.replaceState({}, '', url);

        // Show summary container
        const summaryContainer = document.getElementById('resume-summary-container');
        summaryContainer.classList.remove('hidden');
        
        document.getElementById('summary-filename').textContent = resume.original_filename || 'Untitled';
        document.getElementById('summary-date').textContent = `Uploaded ${utils.formatDate(resume.created_at)}`;

        // Enable Clear All button
        document.getElementById('delete-all-history-btn').classList.remove('hidden');

        // Load data
        this.loadLatestAnalysis();
        this.loadAnalysisHistory();
    },

    async startAnalysis() {
        if (!this.selectedResumeId) return;

        const btn = document.getElementById('start-analysis-btn');
        const originalHtml = btn.innerHTML;
        
        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing... (This may take a moment)';
            
            await api.analyzeResume(
                this.selectedResumeId,
                this.isRegenerate
            );
            utils.showNotification('Analysis complete!', 'success');
            
            // Reload to show results
            await this.loadLatestAnalysis();
            await this.loadAnalysisHistory();
            
        } catch (error) {
            console.error("Error analyzing resume:", error);
            utils.showNotification(error.message || 'Failed to generate analysis.', 'error');
        } finally {
            btn.disabled = false;
            await this.loadLatestAnalysis();
        }
    },

    async loadLatestAnalysis() {
        const container = document.getElementById('latest-analysis-container');
        if (!this.selectedResumeId) return;

        try {
            container.innerHTML = `
                <div class="flex justify-center py-16">
                    <i class="fa-solid fa-spinner fa-spin text-primary text-4xl"></i>
                </div>
            `;

            const analysis = await api.getLatestAnalysis(this.selectedResumeId);
            
            if (!analysis) {
                this.renderEmptyLatestAnalysis();
                return;
            }

            this.renderLatestAnalysis(analysis);

        } catch (error) {
            console.error("Error loading latest analysis:", error);
            // Backend might return 404 if no analysis exists
            this.renderEmptyLatestAnalysis();
        }
    },

    renderEmptyLatestAnalysis() {
    this.isRegenerate = false;

    const analyzeBtn = document.getElementById('start-analysis-btn');

    if (analyzeBtn) {
        analyzeBtn.innerHTML = `
            <i class="fa-solid fa-wand-magic-sparkles"></i>
            Analyze Resume
        `;
    }

    const container = document.getElementById('latest-analysis-container');

    container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-16 text-center">
            <div class="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center mb-4">
                <i class="fa-solid fa-chart-pie text-3xl text-gray-600"></i>
            </div>
            <h3 class="text-xl font-medium text-white mb-2">
                No Analysis Available
            </h3>
            <p class="text-gray-400 max-w-sm mx-auto">
                Click "Analyze Resume" to generate intelligent feedback for this document.
            </p>
        </div>
    `;
},

    getScoreClass(score) {
        if (typeof score !== 'number' || isNaN(score)) return 'neutral';
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        return 'low';
    },

    renderLatestAnalysis(analysis) {
        this.isRegenerate = true;
        const container = document.getElementById('latest-analysis-container');
        const analyzeBtn = document.getElementById('start-analysis-btn');

        if (analyzeBtn) {
            analyzeBtn.innerHTML = `
                <i class="fa-solid fa-rotate-right"></i>
                Regenerate Analysis
            `;
        }
        
        // We only render fields that exist on the backend object. We don't invent fields.
        const score = analysis.score !== undefined && analysis.score !== null ? analysis.score : 'N/A';
        const scoreClass = this.getScoreClass(analysis.score);
        const safeSummary = this.escapeHTML(analysis.summary || 'Analysis complete.');
        const date = utils.formatDate(analysis.created_at);

        let html = `
            <div class="flex flex-col md:flex-row gap-6 items-start">
                <div class="flex flex-col items-center shrink-0">
                    <div class="score-badge ${scoreClass} mb-2">
                        ${this.escapeHTML(score)}
                    </div>
                    <span class="text-xs text-gray-400 font-medium uppercase tracking-wider">Overall Score</span>
                </div>
                
                <div class="flex-1 min-w-0">
                    <h3 class="text-xl font-bold text-white mb-2">Executive Summary</h3>
                    <p class="text-gray-300 mb-4 leading-relaxed">${safeSummary}</p>
                    <p class="text-xs text-gray-500">Generated on ${date}</p>
                </div>
            </div>
        `;

        // Render extra fields dynamically
        const excludedFields = ['id', 'created_at', 'updated_at', 'resume_id', 'score', 'summary', 'status'];
        let extrasHtml = '';
        
        for (const [key, value] of Object.entries(analysis)) {
            if (excludedFields.includes(key) || value === null || value === undefined || value === '') continue;

            const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            let content = '';
            
            if (Array.isArray(value)) {
                if (value.length === 0) continue;
                content = `<ul class="list-disc pl-5 space-y-1 text-gray-300 text-sm mt-2 overflow-wrap-break-word">
                    ${value.map(item => `<li>${this.escapeHTML(typeof item === 'object' ? JSON.stringify(item) : item)}</li>`).join('')}
                </ul>`;
            } else if (typeof value === 'object') {
                content = `<pre class="text-gray-300 text-sm mt-2 overflow-x-auto p-2 bg-gray-900 rounded">${this.escapeHTML(JSON.stringify(value, null, 2))}</pre>`;
            } else {
                content = `<p class="text-gray-300 text-sm mt-2 overflow-wrap-break-word">${this.escapeHTML(value)}</p>`;
            }
            
            extrasHtml += `
                <div class="mt-6 pt-4 border-t border-gray-800 detail-section">
                    <h4 class="font-semibold text-white mb-2">${title}</h4>
                    ${content}
                </div>
            `;
        }

        container.innerHTML = html + extrasHtml;
    },

    async loadAnalysisHistory() {
        const container = document.getElementById('history-container');
        if (!this.selectedResumeId) return;

        try {
            container.innerHTML = `
                <div class="flex justify-center py-8">
                    <i class="fa-solid fa-spinner fa-spin text-primary text-2xl"></i>
                </div>
            `;

            const history = await api.getResumeAnalyses(this.selectedResumeId);

            if (!history || history.length === 0) {
                container.innerHTML = `
                    <div class="p-6 text-center text-gray-500 text-sm">
                        No previous analyses found for this resume.
                    </div>
                `;
                document.getElementById('delete-all-history-btn').classList.add('hidden');
                return;
            }

            // Sort newest first
            const sortedHistory = [...history].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
            document.getElementById('delete-all-history-btn').classList.remove('hidden');

            container.innerHTML = '';
            sortedHistory.forEach(item => {
                const date = utils.formatDate(item.created_at);
                const score = item.score !== undefined ? item.score : '-';
                const status = item.status ? `<span class="px-2 py-0.5 bg-gray-800 text-xs rounded border border-gray-700">${this.escapeHTML(item.status)}</span>` : '';
                
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                    <div class="flex items-center gap-3 min-w-0">
                        <div class="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0 font-bold text-xs">
                            ${this.escapeHTML(score)}
                        </div>
                        <div class="min-w-0">
                            <div class="flex items-center gap-2">
                                <p class="text-sm text-white font-medium truncate">${date}</p>
                                ${status}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-1 shrink-0 ml-4">
                        <button type="button" class="action-btn view h-8 w-8 text-sm" data-action="view" data-id="${this.escapeHTML(item.id)}" aria-label="View Details" title="View Details">
                            <i class="fa-solid fa-eye" aria-hidden="true"></i>
                        </button>
                        <button type="button" class="action-btn delete h-8 w-8 text-sm" data-action="delete" data-id="${this.escapeHTML(item.id)}" aria-label="Delete Analysis" title="Delete Analysis">
                            <i class="fa-solid fa-trash" aria-hidden="true"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            });

        } catch (error) {
            console.error("Error loading analysis history:", error);
            container.innerHTML = `
                <div class="p-6 text-center text-red-400 text-sm">
                    Failed to load history.
                </div>
            `;
        }
    },

    openModal(modalId) {
        this.lastFocusedElement = document.activeElement;
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            modal.setAttribute('aria-hidden', 'false');
            const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable) focusable.focus();
        }
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
        }
        
        if (modalId === 'delete-modal') this.currentDeleteId = null;
        
        if (this.lastFocusedElement) {
            this.lastFocusedElement.focus();
            this.lastFocusedElement = null;
        }
    },

    openDeleteModal(id) {
        this.currentDeleteId = id;
        this.openModal('delete-modal');
    },

    async handleDelete() {
        if (!this.currentDeleteId) return;
        const btn = document.getElementById('confirm-delete-btn');
        const originalText = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            await api.deleteAnalysis(this.currentDeleteId);
            
            utils.showNotification('Analysis deleted.', 'success');
            this.closeModal('delete-modal');
            
            await this.loadLatestAnalysis();
            await this.loadAnalysisHistory();
        } catch (error) {
            console.error("Error deleting analysis:", error);
            utils.showNotification(error.message || 'Failed to delete.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    },

    async handleDeleteAllHistory() {
        if (!this.selectedResumeId) return;
        const btn = document.getElementById('confirm-delete-all-btn');
        const originalText = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            await api.deleteResumeAnalysis(this.selectedResumeId);
            
            utils.showNotification('All analyses cleared.', 'success');
            this.closeModal('delete-all-modal');
            
            await this.loadLatestAnalysis();
            await this.loadAnalysisHistory();
        } catch (error) {
            console.error("Error clearing all history:", error);
            utils.showNotification(error.message || 'Failed to clear history.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    },

    async openDetailsModal(id) {
        this.openModal('details-modal');
        const body = document.getElementById('details-modal-body');
        body.innerHTML = '<div class="text-center py-10"><i class="fa-solid fa-spinner fa-spin text-primary text-3xl" aria-hidden="true"></i></div>';

        try {
            const analysis = await api.getAnalysis(id);
            
            let html = '';
            // Render every field returned by backend gracefully, without inventing logic
            const date = utils.formatDate(analysis.created_at);
            
            html += `
                <div class="mb-4 pb-4 border-b border-gray-800 flex justify-between items-center">
                    <div>
                        <h4 class="text-white font-medium">Record ID: <span class="text-gray-400 font-normal text-sm">${this.escapeHTML(analysis.id)}</span></h4>
                        <p class="text-xs text-gray-500">${date}</p>
                    </div>
                    ${analysis.score !== undefined ? `<div class="score-badge ${this.getScoreClass(analysis.score)} h-10 w-10 text-base">${this.escapeHTML(analysis.score)}</div>` : ''}
                </div>
            `;

            // Loop through keys and render
            for (const [key, value] of Object.entries(analysis)) {
                // Skip common metadata fields we already handled or don't want to list verbosely
                if (['id', 'created_at', 'updated_at', 'resume_id', 'score'].includes(key)) continue;
                
                if (value === null || value === undefined || value === '') continue;

                const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                let content = '';
                if (Array.isArray(value)) {
                    if (value.length === 0) continue;
                    content = `<ul>${value.map(v => `<li>${this.escapeHTML(typeof v === 'object' ? JSON.stringify(v) : v)}</li>`).join('')}</ul>`;
                } else if (typeof value === 'object') {
                    content = `<pre class="text-xs overflow-x-auto p-2 bg-gray-900 rounded">${this.escapeHTML(JSON.stringify(value, null, 2))}</pre>`;
                } else {
                    content = `<p>${this.escapeHTML(value)}</p>`;
                }

                html += `
                    <div class="detail-section">
                        <h4>${this.escapeHTML(title)}</h4>
                        ${content}
                    </div>
                `;
            }

            if (!html) html = '<p class="text-gray-400 text-center">No detailed information available.</p>';
            body.innerHTML = html;

        } catch (error) {
            console.error("Error loading details modal:", error);
            body.innerHTML = `
                <div class="text-center py-6 text-red-400">
                    <i class="fa-solid fa-circle-exclamation text-3xl mb-2" aria-hidden="true"></i>
                    <p>Failed to load details.</p>
                </div>
            `;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    analysisManager.init();
});
