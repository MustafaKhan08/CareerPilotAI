// AI Mock Interview Logic

const interviewManager = {
    currentSessionId: null,
    totalQuestions: 0,
    currentQuestionNumber: 0,

    async init() {
        try {
            await this.loadUIComponents();
            this.bindEvents();
        } catch (error) {
            console.error("Interview initialization failed:", error);
            utils.showNotification('Failed to initialize Mock Interview.', 'error');
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
        const configForm = document.getElementById('config-form');
        if (configForm) {
            configForm.addEventListener('submit', this.handleStartInterview.bind(this));
        }

        const answerForm = document.getElementById('answer-form');
        if (answerForm) {
            answerForm.addEventListener('submit', this.handleAnswerSubmission.bind(this));
        }

        const pdfBtn = document.getElementById('download-pdf-btn');
        if (pdfBtn) {
            pdfBtn.addEventListener('click', this.handleDownloadPDF.bind(this));
        }
    },

    escapeHTML(str) {
        if (!str && str !== 0) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    switchState(stateId) {
        const states = ['config-state', 'live-state', 'loading-state', 'report-state'];
        states.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === stateId) {
                    el.classList.remove('hidden');
                    // Focus management for accessibility
                    el.querySelector('button, [href], input, select, textarea')?.focus();
                } else {
                    el.classList.add('hidden');
                }
            }
        });
        
        // Scroll to top
        const mainScroll = document.getElementById('main-scroll-area');
        if (mainScroll) mainScroll.scrollTop = 0;
    },

    setLoading(message) {
        const msgEl = document.getElementById('loading-message');
        if (msgEl) msgEl.textContent = message || 'Processing...';
        this.switchState('loading-state');
    },

    async handleStartInterview(e) {
        e.preventDefault();
        
        const form = e.target;
        const btn = document.getElementById('start-btn');
        const originalHtml = btn.innerHTML;

        const formData = new FormData(form);
        const payload = {
            target_role: formData.get('target_role').trim(),
            interview_type: formData.get('interview_type'),
            difficulty: formData.get('difficulty'),
            total_questions: Number(formData.get('total_questions'))
        };
        
        const title = formData.get('title').trim();
        // The backend InterviewStartRequest schema strictly requires title: str = Field(min_length=1). 
        // We must provide a fallback if the user leaves it blank to avoid 422 errors.
        if (title) payload.title = title;
        else payload.title = `${payload.target_role} Interview`; 

        // Validation including explicit numeric check for total_questions (1-20 enforced by backend)
        if (!payload.target_role || !payload.interview_type || !payload.difficulty || !Number.isFinite(payload.total_questions) || payload.total_questions < 1 || payload.total_questions > 20) {
            utils.showNotification('Please fill all required fields correctly (1-20 questions).', 'warning');
            return;
        }

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Starting...';
            this.setLoading('Preparing your mock interview...');
            
            // Backend returns InterviewSessionStartResponse
            const response = await api.startInterview(payload);
            
            this.currentSessionId = response.session_id;
            this.totalQuestions = payload.total_questions;
            
            this.renderQuestion(
                response.question_number,
                response.question,
                response.category
            );
            
            this.switchState('live-state');
            utils.showNotification('Interview started successfully.', 'success');
            
        } catch (error) {
            console.error("Error starting interview:", error);
            utils.showNotification(error.message || 'Failed to start interview.', 'error');
            this.switchState('config-state');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    renderQuestion(number, questionText, category) {
        this.currentQuestionNumber = number;
        
        document.getElementById('live-session-id').textContent = `Session: #${this.currentSessionId}`;
        document.getElementById('question-counter').textContent = `Question ${number} of ${this.totalQuestions}`;
        
        const catEl = document.getElementById('question-category');
        if (catEl) {
            if (category) {
                catEl.textContent = category;
                catEl.classList.remove('hidden');
            } else {
                catEl.classList.add('hidden');
            }
        }
        
        // Mathematically correct progress reaching 100% at the final question
        const percentage = Math.min(100, Math.max(0, (number / this.totalQuestions) * 100));
        document.getElementById('progress-fill').style.width = `${percentage}%`;
        
        document.getElementById('current-question-text').textContent = questionText;
        
        const textarea = document.getElementById('answer-input');
        if (textarea) {
            textarea.value = '';
            textarea.style.height = ''; // Reset auto-resize height if modified
        }
    },

    async handleAnswerSubmission(e) {
        e.preventDefault();
        
        const textarea = document.getElementById('answer-input');
        const answer = textarea.value.trim();
        
        if (!answer) {
            utils.showNotification('Please provide an answer before submitting.', 'warning');
            return;
        }

        const btn = document.getElementById('submit-answer-btn');
        const originalHtml = btn.innerHTML;

        try {
            btn.disabled = true;
            textarea.disabled = true; // Disable textarea during evaluation
            this.setLoading('Evaluating your response...');
            
            // Backend returns InterviewEvaluationResponse
            const response = await api.submitInterviewAnswer(this.currentSessionId, answer);
            
            if (response.completed) {
                await this.fetchAndRenderReport();
            } else if (response.next_question) {
                // Render next question. Note: Backend InterviewQuestionResponse lacks 'category'
                this.renderQuestion(
                    response.next_question.question_order,
                    response.next_question.question,
                    null
                );
                this.switchState('live-state');
            } else {
                throw new Error("Invalid backend state: neither completed nor next_question provided.");
            }
            
        } catch (error) {
            console.error("Error submitting answer:", error);
            utils.showNotification(error.message || 'Failed to submit answer.', 'error');
            // Revert state to let user try submitting again without losing text
            this.switchState('live-state');
        } finally {
            btn.disabled = false;
            textarea.disabled = false; // Re-enable textarea
            btn.innerHTML = originalHtml;
        }
    },

    async fetchAndRenderReport() {
        this.setLoading('Generating your comprehensive interview report...');
        try {
            const report = await api.getInterviewReport(this.currentSessionId);
            
            // InterviewReportResponse fields
            const hasScore = typeof report.overall_score === 'number' && Number.isFinite(report.overall_score);
            document.getElementById('report-score').textContent = hasScore ? report.overall_score.toFixed(1) : '0.0';
            document.getElementById('report-summary').textContent = report.summary || 'No summary available.';
            document.getElementById('report-recommendations').textContent = report.recommendations || 'No recommendations.';
            document.getElementById('report-readiness').textContent = report.career_readiness || 'N/A';
            
            this.populateList('report-strengths', report.strengths);
            this.populateList('report-weaknesses', report.weaknesses);
            this.populateList('report-next-steps', report.next_steps);
            
            this.switchState('report-state');
            utils.showNotification('Interview completed!', 'success');
            
        } catch (error) {
            console.error("Error fetching report:", error);
            utils.showNotification(error.message || 'Failed to load final report.', 'error');
            // Optionally, we could provide a retry button, but for now we'll just log
        }
    },

    populateList(elementId, itemsArray) {
        const ul = document.getElementById(elementId);
        if (!ul) return;
        
        ul.innerHTML = '';
        if (Array.isArray(itemsArray) && itemsArray.length > 0) {
            itemsArray.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                ul.appendChild(li);
            });
        } else {
            ul.innerHTML = '<li class="text-gray-500 italic">None reported.</li>';
        }
    },

    async handleDownloadPDF() {
        if (!this.currentSessionId) {
            utils.showNotification('No active interview session found.', 'warning');
            return;
        }

        const btn = document.getElementById('download-pdf-btn');
        const originalHtml = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating PDF...';
            
            const blob = await api.downloadInterviewPDF(this.currentSessionId);
            if (!blob) throw new Error("No file returned");

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `Interview_Report_${this.currentSessionId}.pdf`;
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            utils.showNotification('PDF downloaded successfully.', 'success');
            
        } catch (error) {
            console.error("Error downloading PDF:", error);
            utils.showNotification(error.message || 'Failed to download PDF.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    interviewManager.init();
});
