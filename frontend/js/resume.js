// Resume Management Logic

const resumeManager = {
    currentDeleteId: null,
    lastFocusedElement: null,

    async init() {
        try {
            await this.loadUIComponents();
            this.bindEvents();
            await this.loadResumes();
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
                            document.getElementById('mobile-sidebar-toggle').addEventListener('click', this.toggleSidebar.bind(this));
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
        // File Upload Drag & Drop and Change events
        const fileInput = document.getElementById('resume-upload-input');
        const uploadZone = document.getElementById('upload-zone');
        
        if (fileInput && uploadZone) {
            fileInput.addEventListener('change', this.handleFileUpload.bind(this));
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                uploadZone.addEventListener(eventName, () => uploadZone.classList.add('drag-active'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('drag-active'), false);
            });

            uploadZone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files && files.length > 0) {
                    fileInput.files = files; 
                    this.handleFileUpload({ target: fileInput });
                }
            });
        }

        // Delegated events for resume list actions (replaces inline onclick)
        const resumeContainer = document.getElementById('resume-list-container');
        if (resumeContainer) {
            resumeContainer.addEventListener('click', (e) => {
                const actionBtn = e.target.closest('.action-btn');
                if (!actionBtn) return;
                
                const action = actionBtn.getAttribute('data-action');
                const id = actionBtn.getAttribute('data-id');
                
                if (action === 'view') {
                    this.openDetailsModal(id);
                } else if (action === 'delete') {
                    this.openDeleteModal(id);
                } else if (action === 'analyze') {
                    window.location.href = `/pages/analysis.html?resume_id=${id}`;
                }
            });
        }

        // Modals closing events
        document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeModal('delete-modal');
                this.closeModal('details-modal');
            });
        });

        // Delete confirmation
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', this.handleDelete.bind(this));
        }

        // Accessibility: Close modals with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal('delete-modal');
                this.closeModal('details-modal');
            }
        });
    },

    /**
     * Sanitizes user input to prevent XSS before rendering via innerHTML
     */
    escapeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    async loadResumes() {
        const container = document.getElementById('resume-list-container');
        
        try {
            // Show loading state
            container.innerHTML = `
                <div class="flex justify-center py-10">
                    <i class="fa-solid fa-spinner fa-spin text-primary text-3xl"></i>
                </div>
            `;

            const resumes = await api.listResumes();

            if (!resumes || resumes.length === 0) {
                this.renderEmptyState();
                return;
            }

            // Safely sort a copy of the array without mutating the original API response
            const sortedResumes = [...resumes].sort((a, b) => {
                return new Date(b.created_at || 0) - new Date(a.created_at || 0);
            });

            this.renderResumeList(sortedResumes);

        } catch (error) {
            console.error("Failed to load resumes:", error);
            utils.showNotification("Unable to load resumes. Please try again later.", "error");
            this.renderEmptyState();
        }
    },

    renderEmptyState() {
        const container = document.getElementById('resume-list-container');
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fa-solid fa-folder-open text-gray-600 text-5xl mb-4"></i>
                <h3 class="text-xl font-semibold text-white mb-2">No Resumes Found</h3>
                <p class="text-gray-400 mb-6">You haven't uploaded any resumes yet.</p>
                <label for="resume-upload-input" class="btn btn-primary cursor-pointer hover-scale">
                    <i class="fa-solid fa-upload mr-2"></i> Upload your first resume
                </label>
            </div>
        `;
    },

    renderResumeList(resumes) {
        const container = document.getElementById('resume-list-container');
        container.innerHTML = '';

        resumes.forEach(resume => {
            const card = document.createElement('div');
            card.className = 'resume-card';
            
            const uploadDate = utils.formatDate(resume.created_at);
            const statusText = resume.status ? this.escapeHTML(resume.status) : '';
            const status = statusText ? `<span class="px-2 py-1 bg-gray-700 text-xs rounded-full ml-3">${statusText}</span>` : '';
            const filename = resume.original_filename ? this.escapeHTML(resume.original_filename) : 'Untitled Resume';
            const resumeId = this.escapeHTML(resume.id);

            card.innerHTML = `
                <div class="flex items-center gap-4 flex-1 min-w-0">
                    <div class="w-10 h-10 rounded bg-blue-500/20 text-blue-500 flex items-center justify-center shrink-0">
                        <i class="fa-solid fa-file-pdf" aria-hidden="true"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center">
                            <h4 class="font-medium text-white truncate" title="${filename}">${filename}</h4>
                            ${status}
                        </div>
                        <p class="text-xs text-gray-400 mt-1">Uploaded ${uploadDate}</p>
                    </div>
                </div>
                <div class="flex items-center gap-1 shrink-0 ml-4">
                    <!-- Action buttons use event delegation on parent container -->
                    <button type="button" class="action-btn view" data-action="view" data-id="${resumeId}" aria-label="View Details" title="View Details">
                        <i class="fa-solid fa-eye" aria-hidden="true"></i>
                    </button>
                    <!-- Navigates to analysis module -->
                    <button type="button" class="action-btn analyze" data-action="analyze" data-id="${resumeId}" aria-label="Analyze Resume" title="Analyze Resume">
                        <i class="fa-solid fa-wand-magic-sparkles" aria-hidden="true"></i>
                    </button>
                    <button type="button" class="action-btn delete" data-action="delete" data-id="${resumeId}" aria-label="Delete Resume" title="Delete Resume">
                        <i class="fa-solid fa-trash" aria-hidden="true"></i>
                    </button>
                </div>
            `;
            container.appendChild(card);
        });
    },

    /**
     * Validates file on client side before sending to API
     */
    validateFile(file) {
        if (!file) {
            return "Please select a file to upload.";
        }

        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const validExtensions = ['.pdf', '.doc', '.docx'];
        
        // Check by type or extension
        const isValidType = validTypes.includes(file.type);
        const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

        if (!isValidType && !hasValidExtension) {
            return "Invalid file type. Only PDF and Word documents are supported.";
        }

        // Max size 5MB
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            return "File is too large. Maximum size is 5MB.";
        }

        return null; // Null means valid
    },

    async handleFileUpload(event) {
        const file = event.target.files[0];
        const fileInput = document.getElementById('resume-upload-input');
        
        // Client-side validation
        const validationError = this.validateFile(file);
        if (validationError) {
            utils.showNotification(validationError, 'error');
            fileInput.value = ''; // clear input
            return;
        }

        const uploadLabel = document.getElementById('upload-label');
        const uploadIcon = document.getElementById('upload-icon');
        const safeFilename = this.escapeHTML(file.name);

        try {
            // Loading state
            fileInput.disabled = true;
            uploadIcon.className = "fa-solid fa-spinner fa-spin text-primary text-4xl mb-4";
            uploadLabel.innerHTML = `Uploading <span class="text-white font-medium">${safeFilename}</span>...`;

            // Call API
            await api.uploadResume(file);
            
            utils.showNotification('Resume uploaded successfully.', 'success');
            
            // Reload list
            await this.loadResumes();

        } catch (error) {
            utils.showNotification(error.message || 'Failed to upload resume.', 'error');
        } finally {
            // Restore state
            fileInput.disabled = false;
            fileInput.value = ''; // clear
            uploadIcon.className = "fa-solid fa-cloud-arrow-up text-primary text-4xl mb-4";
            uploadLabel.innerHTML = '<span class="text-primary font-medium">Click to upload</span> or drag and drop<br><span class="text-sm text-gray-500 mt-2 inline-block">PDF, DOCX up to 5MB</span>';
        }
    },

    openDeleteModal(id) {
        this.currentDeleteId = id;
        this.lastFocusedElement = document.activeElement;
        
        const modal = document.getElementById('delete-modal');
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus management
        const cancelBtn = modal.querySelector('.modal-cancel');
        if (cancelBtn) cancelBtn.focus();
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            modal.setAttribute('aria-hidden', 'true');
        }
        if (modalId === 'delete-modal') {
            this.currentDeleteId = null;
        }
        
        // Restore focus
        if (this.lastFocusedElement) {
            this.lastFocusedElement.focus();
            this.lastFocusedElement = null;
        }
    },

    async handleDelete() {
        if (!this.currentDeleteId) return;

        const btn = document.getElementById('confirm-delete-btn');
        const originalText = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';

            await api.deleteResume(this.currentDeleteId);
            
            utils.showNotification('Resume deleted successfully.', 'success');
            this.closeModal('delete-modal');
            
            // Reload list
            await this.loadResumes();
            
        } catch (error) {
            utils.showNotification(error.message || 'Failed to delete resume.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    },

    async openDetailsModal(id) {
        this.lastFocusedElement = document.activeElement;
        
        const modal = document.getElementById('details-modal');
        const contentBody = document.getElementById('details-modal-body');
        
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        
        contentBody.innerHTML = '<div class="text-center py-8"><i class="fa-solid fa-spinner fa-spin text-2xl text-primary" aria-hidden="true"></i></div>';

        try {
            const resume = await api.getResume(id);
            
            const safeFilename = this.escapeHTML(resume.original_filename || 'Untitled');
            const safeStatus = this.escapeHTML(resume.status || 'Processed');
            const safeParsedContent = resume.parsed_content ? this.escapeHTML(resume.parsed_content) : null;
            
            // Render available data safely
            contentBody.innerHTML = `
                <div class="space-y-4">
                    <div class="flex items-center gap-3 pb-4 border-b border-gray-800">
                        <i class="fa-solid fa-file-pdf text-3xl text-red-400" aria-hidden="true"></i>
                        <div>
                            <h3 class="font-semibold text-lg text-white">${safeFilename}</h3>
                            <p class="text-sm text-gray-400">Uploaded ${utils.formatDate(resume.created_at)}</p>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="text-sm font-medium text-gray-400 mb-1">Status</h4>
                        <p class="text-white">${safeStatus}</p>
                    </div>
                    
                    ${safeParsedContent ? `
                    <div>
                        <h4 class="text-sm font-medium text-gray-400 mb-1">Parsed Snippet</h4>
                        <div class="bg-gray-800/50 p-3 rounded text-sm text-gray-300 max-h-40 overflow-y-auto">
                            ${safeParsedContent}
                        </div>
                    </div>` : ''}
                    
                    <div class="pt-4 border-t border-gray-800 flex justify-end">
                        <button type="button" class="btn btn-primary modal-close-internal hover-scale focus-visible:ring-2 focus-visible:ring-primary" onclick="resumeManager.closeModal('details-modal')">Close</button>
                    </div>
                </div>
            `;
            
            // Focus management inside modal
            const closeBtn = contentBody.querySelector('.modal-close-internal');
            if (closeBtn) closeBtn.focus();
            
        } catch (error) {
            contentBody.innerHTML = `
                <div class="text-center py-6 text-red-400">
                    <i class="fa-solid fa-circle-exclamation text-3xl mb-2" aria-hidden="true"></i>
                    <p>Failed to load resume details.</p>
                </div>
            `;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    resumeManager.init();
});
