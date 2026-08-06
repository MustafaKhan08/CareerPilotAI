// Dashboard Logic

const dashboard = {
    /**
     * Initialize the dashboard data fetching and UI rendering
     */
    async init() {
        try {
            await this.loadUIComponents();
            await Promise.all([
                this.loadWelcomeSection(),
                this.loadDashboardData()
            ]);
        } catch (error) {
            console.error("Dashboard initialization failed:", error);
            utils.showNotification("Failed to load some dashboard data.", "error");
        }
    },

    /**
     * Loads the Sidebar and Navbar dynamically and binds their events
     */
    async loadUIComponents() {
        // Load Sidebar
        await new Promise(resolve => {
            utils.loadComponent('sidebar-container', '../components/sidebar.html', () => {
                this.initSidebarLogic();
                resolve();
            });
        });

        // Load Navbar
        await new Promise(resolve => {
            utils.loadComponent('navbar-container', '../components/navbar.html', () => {
                const nav = document.querySelector('nav');
                if (nav) {
                    nav.classList.add('px-6', 'lg:px-10'); // Adjust padding for dashboard view
                    // Add sidebar toggle button to navbar for mobile
                    const toggleBtnHtml = `
                        <button class="md:hidden text-white mr-4" id="mobile-sidebar-toggle" aria-label="Open Sidebar">
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
        });
    },

    /**
     * Highlights active sidebar link and binds mobile toggle events
     */
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

    /**
     * Toggles the sidebar visibility on mobile
     */
    toggleSidebar() {
        const sidebar = document.getElementById('app-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && overlay) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        }
    },

    /**
     * Loads the welcome section with the user's name
     */
    async loadWelcomeSection() {
        const user = storage.getUser();
        const welcomeName = document.getElementById('welcome-name');
        
        if (user && user.full_name) {
            welcomeName.textContent = user.full_name.split(' ')[0]; // First name
        } else {
            // Fallback: fetch from API if not in storage
            try {
                const fetchedUser = await api.getCurrentUser();
                storage.setUser(fetchedUser);
                welcomeName.textContent = fetchedUser.full_name.split(' ')[0];
            } catch (err) {
                welcomeName.textContent = "User";
            }
        }
    },

    /**
     * Fetches resumes and jobs to populate stats and recent cards
     */
    async loadDashboardData() {
        try {
            const [resumes, jobs] = await Promise.all([
                api.listResumes().catch(() => []),
                api.listJobs().catch(() => [])
            ]);

            // Update Stats
            document.getElementById('stat-resumes').textContent = resumes.length;
            document.getElementById('stat-jobs').textContent = jobs.length;
            
            // Stats without backend endpoints currently get an N/A professional state
            document.getElementById('stat-interviews').textContent = "—"; 

            // Find the true latest resume by sorting if created_at is available
            const latestResume = this.getLatestResume(resumes);

            // Update Recent Resume
            this.renderRecentResume(latestResume);
            
            // Update Latest Analysis
            await this.renderLatestAnalysis(latestResume);
            
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        }
    },

    /**
     * Returns the most recent resume by comparing created_at timestamps.
     */
    getLatestResume(resumes) {
        if (!resumes || resumes.length === 0) return null;
        
        // Sort descending to ensure the first element is the newest
        return [...resumes].sort((a, b) => {
            const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
            const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
            return dateB - dateA;
        })[0];
    },

    /**
     * Renders the most recently uploaded resume
     */
    renderRecentResume(latest) {
        const container = document.getElementById('recent-resume-container');
        
        if (!latest) {
            container.innerHTML = `
                <div class="text-center py-6">
                    <div class="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4 text-gray-500">
                        <i class="fa-solid fa-file-pdf text-2xl"></i>
                    </div>
                    <p class="text-gray-400 mb-4">You haven't uploaded any resumes yet.</p>
                    <a href="/pages/resume.html" class="btn btn-primary text-sm px-4 py-2">Upload Resume</a>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="flex items-start gap-4">
                <div class="w-12 h-12 rounded bg-blue-500/20 text-blue-500 flex items-center justify-center shrink-0">
                    <i class="fa-solid fa-file-lines text-xl"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <h4 class="font-medium text-white truncate" title="${latest.filename || 'Resume'}">${latest.filename || 'Resume.pdf'}</h4>
                    <p class="text-xs text-gray-400 mt-1">Uploaded ${utils.formatDate(latest.created_at || new Date().toISOString())}</p>
                </div>
                <a href="/pages/resume.html" class="text-primary hover:text-white transition">
                    <i class="fa-solid fa-arrow-right"></i>
                </a>
            </div>
        `;
    },

    /**
     * Fetches and renders the latest analysis for the most recent resume
     */
    async renderLatestAnalysis(latestResume) {
        const container = document.getElementById('latest-analysis-container');
        
        if (!latestResume) {
            this.renderEmptyAnalysis(container);
            return;
        }
        
        try {
            const analysis = await api.getLatestAnalysis(latestResume.id);
            
            if (!analysis) {
                this.renderEmptyAnalysis(container);
                return;
            }

            // Render snippet of analysis
            container.innerHTML = `
                <div class="mb-3">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-sm font-medium text-gray-300">Overall Score</span>
                        <span class="text-accent font-bold">${analysis.score || 'N/A'}/100</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-accent h-2 rounded-full" style="width: ${analysis.score || 0}%"></div>
                    </div>
                </div>
                <p class="text-sm text-gray-400 line-clamp-2 mt-4">
                    ${analysis.summary || 'Analysis complete. Click to view detailed feedback on strengths and areas for improvement.'}
                </p>
                <div class="mt-4">
                    <a href="/pages/resume.html" class="text-primary text-sm font-medium hover:underline">View Full Analysis &rarr;</a>
                </div>
            `;
            
        } catch (error) {
            // API might return 404 if no analysis exists
            this.renderEmptyAnalysis(container);
        }
    },
    
    renderEmptyAnalysis(container) {
        container.innerHTML = `
            <div class="text-center py-6">
                <i class="fa-solid fa-chart-line text-gray-600 text-3xl mb-3"></i>
                <p class="text-gray-400 text-sm">No analysis available yet.</p>
                <p class="text-gray-500 text-xs mt-1">Upload a resume to get started.</p>
            </div>
        `;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Only init if we are on the dashboard
    dashboard.init();
});
