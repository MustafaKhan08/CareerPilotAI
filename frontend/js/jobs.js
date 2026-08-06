// Jobs Module Logic

const jobsManager = {
    jobsList: [],
    currentPage: 1,
    pageSize: 20,
    totalPages: 0,
    totalJobs: 0,
    currentSearchQuery: '',
    searchDebounceTimer: null,
    currentDeleteId: null,
    lastFocusedElement: null,

    async init() {
        try {
            await this.loadUIComponents();
            this.bindEvents();
            await this.loadJobs();
        } catch (error) {
            console.error("Jobs initialization failed:", error);
            utils.showNotification('Failed to initialize Jobs module.', 'error');
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
        // Toggle Create Job Panel
        document.getElementById('toggle-create-btn')?.addEventListener('click', () => {
            document.getElementById('create-job-panel')?.classList.add('active');
        });
        
        document.getElementById('close-create-btn')?.addEventListener('click', () => {
            document.getElementById('create-job-panel')?.classList.remove('active');
        });

        document.getElementById('cancel-create-btn')?.addEventListener('click', () => {
            document.getElementById('create-job-panel')?.classList.remove('active');
            document.getElementById('create-job-form')?.reset();
        });

        // Create Form Submission
        document.getElementById('create-job-form')?.addEventListener('submit', this.handleCreateJob.bind(this));

        // Import Button
        document.getElementById('import-jobs-btn')?.addEventListener('click', this.handleImportJobs.bind(this));

        // Search Input (Debounced)
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                this.currentSearchQuery = query;
                
                if (this.searchDebounceTimer) clearTimeout(this.searchDebounceTimer);
                
                this.searchDebounceTimer = setTimeout(() => {
                    if (query.length > 0) {
                        this.searchJobs(query, 1);
                    } else {
                        this.currentPage = 1;
                        this.loadJobs();
                    }
                }, 400); // 400ms debounce
            });
        }

        // List Action Buttons Delegation
        const container = document.getElementById('jobs-container');
        if (container) {
            container.addEventListener('click', (e) => {
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

        // Delete Confirmation
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', this.handleDeleteJob.bind(this));
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

    setLoadingState(isLoading, isSearch = false) {
        if (isSearch) {
            const loader = document.getElementById('search-loading');
            if (isLoading) loader?.classList.remove('hidden');
            else loader?.classList.add('hidden');
        } else {
            const overlay = document.getElementById('jobs-loading-overlay');
            if (isLoading) overlay?.classList.remove('hidden');
            else overlay?.classList.add('hidden');
        }
    },

    async loadJobs(page = this.currentPage) {
        this.setLoadingState(true);
        try {
            this.currentPage = page;
            const response = await api.listJobs(this.currentPage, this.pageSize);
            
            this.jobsList = response.items || [];
            this.totalPages = response.total_pages || 0;
            this.totalJobs = response.total || 0;
            
            this.renderJobs(this.jobsList);
            this.renderPagination();
        } catch (error) {
            console.error("Error loading jobs:", error);
            this.renderEmptyState('Failed to load jobs.', 'error');
            utils.showNotification('Could not load jobs.', 'error');
        } finally {
            this.setLoadingState(false);
        }
    },

    async searchJobs(query, page = this.currentPage) {
        this.currentSearchId = (this.currentSearchId || 0) + 1;
        const searchId = this.currentSearchId;
        
        this.setLoadingState(true, true);
        try {
            this.currentPage = page;
            const response = await api.searchJobs({ query: query, page: this.currentPage, limit: this.pageSize });
            
            if (this.currentSearchId !== searchId) return;

            this.jobsList = response.items || [];
            this.totalPages = response.total_pages || 0;
            this.totalJobs = response.total || 0;
            
            this.renderJobs(this.jobsList, true);
            this.renderPagination();
        } catch (error) {
            if (this.currentSearchId !== searchId) return;
            console.error("Error searching jobs:", error);
            this.renderEmptyState('Search failed.', 'error');
        } finally {
            if (this.currentSearchId === searchId) {
                this.setLoadingState(false, true);
            }
        }
    },

    renderJobs(jobs, isSearch = false) {
        const container = document.getElementById('jobs-container');
        if (!container) return;

        // Clear existing (excluding loading overlay)
        Array.from(container.children).forEach(child => {
            if (child.id !== 'jobs-loading-overlay') {
                child.remove();
            }
        });

        if (!jobs || jobs.length === 0) {
            const emptyMsg = isSearch ? `No jobs found matching "${this.escapeHTML(this.currentSearchQuery)}"` : "No jobs available. Create or import one to get started.";
            this.renderEmptyState(emptyMsg);
            return;
        }

        jobs.forEach(job => {
            const id = this.escapeHTML(job.id);
            const title = this.escapeHTML(job.job_title || 'Untitled Position');
            const company = this.escapeHTML(job.company_name || 'Unknown Company');
            
            // Build dynamic tags if they exist
            let tagsHtml = '';
            if (job.location) tagsHtml += `<span class="job-tag"><i class="fa-solid fa-location-dot" aria-hidden="true"></i> ${this.escapeHTML(job.location)}</span>`;
            if (job.job_type) tagsHtml += `<span class="job-tag"><i class="fa-solid fa-briefcase" aria-hidden="true"></i> ${this.escapeHTML(job.job_type)}</span>`;
            
            // If it's a search result, it might have similarity_score
            if (job.similarity_score !== undefined && job.similarity_score !== null) {
                const score = (job.similarity_score * 100).toFixed(0);
                tagsHtml += `<span class="similarity-badge"><i class="fa-solid fa-bolt" aria-hidden="true"></i> ${this.escapeHTML(score)}% Match</span>`;
            }

            // Description or summary preview
            const desc = this.escapeHTML(job.job_description || job.combined_text || 'No description available.');

            const cardHtml = `
                <div class="job-card" data-job-id="${id}">
                    <div class="job-card-header">
                        <div class="min-w-0">
                            <h3 class="job-title">${title}</h3>
                            <p class="job-company">${company}</p>
                        </div>
                    </div>
                    
                    ${tagsHtml ? `<div class="job-tags">${tagsHtml}</div>` : ''}
                    
                    <p class="job-desc-preview">${desc}</p>
                    
                    <div class="job-actions">
                        <button type="button" class="action-btn view" data-action="view" data-id="${id}" aria-label="View Details" title="View Details">
                            <i class="fa-solid fa-eye" aria-hidden="true"></i>
                        </button>
                        <button type="button" class="action-btn delete" data-action="delete" data-id="${id}" aria-label="Delete Job" title="Delete Job">
                            <i class="fa-solid fa-trash" aria-hidden="true"></i>
                        </button>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', cardHtml);
        });
    },

    renderPagination() {
        const container = document.getElementById('pagination-container');
        if (!container) return;

        if (this.totalJobs === 0) {
            container.innerHTML = '';
            return;
        }

        const start = (this.currentPage - 1) * this.pageSize + 1;
        const end = Math.min(this.currentPage * this.pageSize, this.totalJobs);

        const html = `
            <div class="pagination-info">
                <span class="font-medium text-white">Showing ${start}–${end} of ${this.totalJobs} jobs</span>
                <span>Page ${this.currentPage} of ${this.totalPages}</span>
            </div>
            <div class="flex gap-3">
                <button type="button" id="prev-page-btn" class="pagination-btn" ${this.currentPage <= 1 ? 'disabled' : ''}>
                    <i class="fa-solid fa-chevron-left"></i> Previous
                </button>
                <button type="button" id="next-page-btn" class="pagination-btn" ${this.currentPage >= this.totalPages ? 'disabled' : ''}>
                    Next <i class="fa-solid fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        container.innerHTML = html;

        const prevBtn = document.getElementById('prev-page-btn');
        const nextBtn = document.getElementById('next-page-btn');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.goToPage(this.currentPage - 1);
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.currentPage < this.totalPages) {
                    this.goToPage(this.currentPage + 1);
                }
            });
        }
    },

    async goToPage(page) {
        if (this.currentSearchQuery) {
            await this.searchJobs(this.currentSearchQuery, page);
        } else {
            await this.loadJobs(page);
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    renderEmptyState(message, type = 'default') {
        const container = document.getElementById('jobs-container');
        if (!container) return;
        
        let icon = 'fa-inbox';
        let colorClass = 'text-gray-500';
        
        if (type === 'error') {
            icon = 'fa-triangle-exclamation';
            colorClass = 'text-red-400';
        }

        const emptyHtml = `
            <div class="col-span-full py-16 flex flex-col items-center justify-center text-center">
                <div class="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center mb-4">
                    <i class="fa-solid ${icon} text-3xl ${colorClass}" aria-hidden="true"></i>
                </div>
                <h3 class="text-xl font-medium text-white mb-2">${type === 'error' ? 'Error' : 'Empty'}</h3>
                <p class="text-gray-400 max-w-sm mx-auto">${this.escapeHTML(message)}</p>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', emptyHtml);
    },

    async handleCreateJob(e) {
        e.preventDefault();
        
        const form = e.target;
        const btn = document.getElementById('submit-job-btn');
        const originalHtml = btn.innerHTML;
        
        const formData = new FormData(form);
        const jobData = {};
        
        formData.forEach((value, key) => {
            if (value.trim() !== '') {
                // Parse numeric fields properly, avoiding NaN
                if (key === 'salary_from' || key === 'salary_to' || key === 'employees') {
                    const num = Number(value);
                    if (!isNaN(num)) {
                        jobData[key] = num;
                    }
                } else {
                    jobData[key] = value.trim();
                }
            }
        });

        // Auto-generate combined_text for backend indexing before submission
        jobData.combined_text = [jobData.job_title, jobData.company_name, jobData.job_description, jobData.industry, jobData.location, jobData.job_type]
            .filter(Boolean)
            .join(' ');

        // Basic client validation
        if (!jobData.job_title || !jobData.job_description) {
            utils.showNotification('Please fill all required fields.', 'warning');
            return;
        }

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            
            await api.createJob(jobData);
            
            utils.showNotification('Job created successfully.', 'success');
            form.reset();
            document.getElementById('create-job-panel')?.classList.remove('active');
            
            // Refresh list preserving search state and page
            if (this.currentSearchQuery) {
                await this.searchJobs(this.currentSearchQuery, this.currentPage);
            } else {
                await this.loadJobs(this.currentPage);
            }
            
        } catch (error) {
            console.error("Error creating job:", error);
            utils.showNotification(error.message || 'Failed to create job.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async handleImportJobs() {
        const btn = document.getElementById('import-jobs-btn');
        const originalHtml = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Importing...';
            
            const response = await api.importJobs({}); // Backend accepts no body or empty dict
            
            const msg = response.message || 'Job import completed.';
            const imported = response.imported !== undefined ? response.imported : 0;
            const skipped = response.skipped !== undefined ? response.skipped : 0;
            
            utils.showNotification(`${msg} (${imported} imported, ${skipped} skipped)`, 'success');
            
            // Refresh list preserving search state and page
            if (this.currentSearchQuery) {
                await this.searchJobs(this.currentSearchQuery, this.currentPage);
            } else {
                await this.loadJobs(this.currentPage);
            }
            
        } catch (error) {
            console.error("Error importing jobs:", error);
            utils.showNotification(error.message || 'Import failed.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async openDetailsModal(id) {
        this.openModal('details-modal');
        const body = document.getElementById('details-modal-body');
        const titleEl = document.getElementById('details-modal-title');
        const subtitleEl = document.getElementById('details-modal-subtitle');
        const applyBtn = document.getElementById('modal-apply-btn');
        
        body.innerHTML = '<div class="text-center py-16"><i class="fa-solid fa-circle-notch fa-spin text-primary text-4xl"></i></div>';
        applyBtn.classList.add('hidden');
        titleEl.textContent = 'Loading...';
        subtitleEl.textContent = '';

        try {
            const job = await api.getJob(id);
            
            titleEl.textContent = job.job_title || 'Job Details';
            subtitleEl.textContent = job.company_name || 'Unknown Company';
            
            if (job.apply_url) {
                applyBtn.href = job.apply_url;
                applyBtn.classList.remove('hidden');
            }

            // Exclude common structural/internal keys from generic rendering
            const excludedKeys = ['id', 'job_title', 'company_name', 'apply_url', 'created_at', 'updated_at', 'combined_text'];
            
            let html = '';
            
            for (const [key, value] of Object.entries(job)) {
                if (excludedKeys.includes(key) || value === null || value === undefined || value === '') continue;
                
                const displayTitle = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                let content = '';
                if (Array.isArray(value)) {
                    if (value.length === 0) continue;
                    content = `<ul class="list-disc pl-5 space-y-1">${value.map(v => `<li>${this.escapeHTML(typeof v === 'object' ? JSON.stringify(v) : v)}</li>`).join('')}</ul>`;
                } else if (typeof value === 'object') {
                    content = `<pre class="text-xs overflow-x-auto p-2 bg-gray-900 rounded">${this.escapeHTML(JSON.stringify(value, null, 2))}</pre>`;
                } else {
                    content = `<p>${this.escapeHTML(value)}</p>`;
                }
                
                html += `
                    <div class="job-detail-row">
                        <h4>${this.escapeHTML(displayTitle)}</h4>
                        ${content}
                    </div>
                `;
            }

            // Add dates securely at the bottom
            const created = job.created_at ? utils.formatDate(job.created_at) : null;
            if (created) {
                html += `
                    <div class="job-detail-row">
                        <h4>Added On</h4>
                        <p>${this.escapeHTML(created)}</p>
                    </div>
                `;
            }

            body.innerHTML = html || '<p class="text-gray-400 p-4">No additional details available.</p>';
            
        } catch (error) {
            console.error("Error fetching job details:", error);
            body.innerHTML = `
                <div class="text-center py-10 text-red-400">
                    <i class="fa-solid fa-triangle-exclamation text-4xl mb-4"></i>
                    <p>Failed to load job details.</p>
                </div>
            `;
            titleEl.textContent = 'Error';
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

    async handleDeleteJob() {
        if (!this.currentDeleteId) return;
        const btn = document.getElementById('confirm-delete-btn');
        const originalHtml = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';
            
            await api.deleteJob(this.currentDeleteId);
            
            utils.showNotification('Job deleted successfully.', 'success');
            this.closeModal('delete-modal');
            
            // Automatically navigate to previous page if we delete the last item on the current page
            if (this.jobsList.length === 1 && this.currentPage > 1) {
                this.currentPage--;
            }

            // Refresh list preserving search state and page
            if (this.currentSearchQuery) {
                await this.searchJobs(this.currentSearchQuery, this.currentPage);
            } else {
                await this.loadJobs(this.currentPage);
            }
            
        } catch (error) {
            console.error("Error deleting job:", error);
            utils.showNotification(error.message || 'Failed to delete job.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    jobsManager.init();
});
