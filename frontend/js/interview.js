// AI Mock Interview Logic

// ==========================================================
// Voice Controller (Web Speech API)
// ==========================================================

const voiceController = {
    recognition: null,
    isListening: false,
    isSupported: false,
    _prefixText: '',

    init() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            this.isSupported = false;
            console.warn('[Voice] SpeechRecognition API not found in this browser.');
            const btn = document.getElementById('mic-btn');
            if (btn) {
                btn.disabled = true;
                btn.title = 'Voice input is not supported in this browser.';
            }
            this._setStatus('Voice input is not supported in this browser.', 'error');
            return;
        }
        console.log('[Voice] SpeechRecognition API found. Initializing...');
        this.isSupported = true;
        try {
            this.recognition = new SR();
        } catch (error) {
            this.isSupported = false;
            console.error('[Voice] Speech recognition initialization failed:', error);
            const btn = document.getElementById('mic-btn');
            if (btn) {
                btn.disabled = true;
                btn.title = 'Voice input could not be initialized.';
            }
            this._setStatus(
                'Voice input could not be initialized. Check browser support and microphone permissions.',
                'error'
            );
            return;
        }
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        console.log('[Voice] Initialized. isSupported:', this.isSupported);

        this.recognition.onresult = (e) => {
            const textarea = document.getElementById('answer-input');
            if (!textarea) return;

            let interim = '';
            let final = '';
            for (let i = 0; i < e.results.length; i++) {
                if (e.results[i].isFinal) {
                    final += e.results[i][0].transcript;
                } else {
                    interim += e.results[i][0].transcript;
                }
            }

            // Append recognized speech to the text that existed before this speech session began
            const spacer = (this._prefixText && !this._prefixText.endsWith(' ') && !this._prefixText.endsWith('\n')) ? ' ' : '';
            textarea.value = this._prefixText + (final || interim ? spacer : '') + final + (final && interim ? ' ' : '') + interim;
        };

        this.recognition.onerror = (e) => {
            const msg = {
                'not-allowed': 'Microphone access denied. Please allow microphone permissions.',
                'no-speech':   'No speech detected. Click the mic to try again.',
                'network':     'Network error during voice recognition.',
                'audio-capture': 'No microphone found.',
            }[e.error] || `Voice error: ${e.error}`;
            this._setStatus(msg, 'error');
            this._setListening(false);
            this.isListening = false;
        };

        this.recognition.onend = () => {
            if (this.isListening) {
                this.isListening = false;
                this._setListening(false);
                this._setStatus('Voice input stopped.', '');
            }
        };
    },

    toggle() {
        console.log('[Voice] toggle() called — isSupported:', this.isSupported, 'isListening:', this.isListening);
        if (!this.isSupported) {
            console.warn('[Voice] toggle() aborted — Speech Recognition not supported or init failed.');
            return;
        }
        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    },

    start() {
        if (!this.isSupported || this.isListening) {
            console.warn('[Voice] start() aborted — isSupported:', this.isSupported, 'isListening:', this.isListening);
            return;
        }

        // Remember current text so spoken speech cleanly appends
        const textarea = document.getElementById('answer-input');
        this._prefixText = textarea ? textarea.value : '';

        try {
            this.recognition.start();
            this.isListening = true;
            this._setListening(true);
            this._setStatus('Listening… speak your answer.', 'listening');
        } catch (err) {
            console.warn('[Voice] start() error:', err);
            this.isListening = false;
            this._setListening(false);
            this._setStatus(
                'Unable to start voice input. Check microphone permissions and try again.',
                'error'
            );
        }
    },

    stop() {
        if (!this.isSupported || !this.isListening) return;
        this.isListening = false;
        try {
            this.recognition.stop();
        } catch (_) {}
        this._setListening(false);
        this._setStatus('Voice input stopped.', '');
    },

    _setListening(active) {
        const btn = document.getElementById('mic-btn');
        const icon = document.getElementById('mic-icon');
        if (!btn || !icon) return;
        if (active) {
            btn.classList.add('listening');
            icon.classList.remove('fa-microphone');
            icon.classList.add('fa-microphone-slash');
            btn.title = 'Stop voice input';
            btn.setAttribute('aria-label', 'Stop voice input');
        } else {
            btn.classList.remove('listening');
            icon.classList.remove('fa-microphone-slash');
            icon.classList.add('fa-microphone');
            btn.title = 'Start voice input';
            btn.setAttribute('aria-label', 'Start voice input');
        }
    },

    _setStatus(msg, type) {
        const el = document.getElementById('voice-status');
        if (!el) return;
        el.textContent = msg;
        el.className = 'voice-status' + (type ? ` ${type}` : '');
        el.classList.remove('hidden');
        if (!msg) el.classList.add('hidden');
    },

    disable() {
        this.stop();
        const btn = document.getElementById('mic-btn');
        if (btn) btn.disabled = true;
    },

    enable() {
        const btn = document.getElementById('mic-btn');
        if (btn) btn.disabled = false;
    }
};

// ==========================================================
// Timer Controller
// ==========================================================

const timerController = {
    _intervalId: null,
    _deadlineMs: null,
    _onExpire: null,

    /**
     * Start countdown toward the given UTC deadline ISO string.
     */
    start(deadlineIso, onExpire) {
        clearInterval(this._intervalId);
        this._intervalId = null;
        const deadlineMs = typeof deadlineIso === 'string'
            ? Date.parse(deadlineIso)
            : NaN;
        console.log('[Timer] start() deadlineIso:', deadlineIso, 'parsed ms:', deadlineMs, 'isFinite:', Number.isFinite(deadlineMs));
        if (!Number.isFinite(deadlineMs)) {
            this.clear();
            const el = document.getElementById('timer-display');
            if (el) el.textContent = 'Unavailable';
            throw new Error(
                'The interview response did not include a valid deadline_at timestamp.'
            );
        }

        this._deadlineMs = deadlineMs;
        this._onExpire = onExpire;
        this._intervalId = setInterval(() => this._tick(), 1000);
        this._tick();
    },

    /** Clear the active timer. */
    clear() {
        clearInterval(this._intervalId);
        this._intervalId = null;
        this._deadlineMs = null;
        this._onExpire = null;
        const el = document.getElementById('interview-timer');
        if (el) el.classList.remove('warning', 'expired');
    },

    _tick() {
        const el = document.getElementById('timer-display');
        const container = document.getElementById('interview-timer');
        if (!el || this._deadlineMs === null) {
            console.warn('[Timer] _tick(): timer-display element not found or _deadlineMs is null. el:', el, '_deadlineMs:', this._deadlineMs);
            return;
        }

        const remaining = Math.max(0, Math.floor((this._deadlineMs - Date.now()) / 1000));
        const mm = String(Math.floor(remaining / 60)).padStart(2, '0');
        const ss = String(remaining % 60).padStart(2, '0');
        el.textContent = `${mm}:${ss}`;

        if (remaining <= 0) {
            clearInterval(this._intervalId);
            this._intervalId = null;
            if (container) {
                container.classList.remove('warning');
                container.classList.add('expired');
            }
            if (this._onExpire) this._onExpire();
        } else if (remaining <= 60) {
            if (container) container.classList.add('warning');
        } else {
            if (container) container.classList.remove('warning');
        }
    }
};

// ==========================================================
// Interview Manager
// ==========================================================

const interviewManager = {
    currentSessionId: null,
    totalQuestions: 0,
    currentQuestionNumber: 0,
    _timerExpiredHandled: false,
    _initialized: false,
    _eventsBound: false,
    SESSION_KEY: 'careerpilot_active_interview',

    async init() {
        if (this._initialized) return;
        this._initialized = true;

        // Bind the interview controls independently of optional shared UI components.
        this.bindEvents();
        voiceController.init();

        try {
            await this.loadUIComponents();
            this.checkRestoredSession();
        } catch (error) {
            console.error("Interview initialization failed:", error);
            utils.showNotification('Failed to initialize Mock Interview.', 'error');
        }
    },

    async loadUIComponents() {
        const loadComponent = async (containerId, componentPath, callback) => {
            try {
                const loaded = await utils.loadComponent(
                    containerId,
                    componentPath,
                    callback
                );
                if (!loaded) {
                    console.warn(
                        `[Interview] Continuing without optional component ${componentPath}.`
                    );
                }
            } catch (error) {
                console.error(
                    `[Interview] Failed to load optional component ${componentPath}:`,
                    error
                );
            }
        };

        await Promise.all([
            loadComponent('sidebar-container', '../components/sidebar.html', () => {
                this.initSidebarLogic();
            }),
            loadComponent('navbar-container', '../components/navbar.html', () => {
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
                        if (toggleBtn) {
                            toggleBtn.addEventListener(
                                'click',
                                this.toggleSidebar.bind(this)
                            );
                        }
                    }
                }
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
        if (this._eventsBound) return;
        this._eventsBound = true;

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

        const micBtn = document.getElementById('mic-btn');
        if (micBtn) {
            micBtn.addEventListener('click', () => voiceController.toggle());
            console.log('[Voice] mic-btn click listener attached.');
        } else {
            console.warn('[Voice] mic-btn element not found during bindEvents().');
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
                    el.querySelector('button, [href], input, select, textarea')?.focus();
                } else {
                    el.classList.add('hidden');
                }
            }
        });

        // Stop voice whenever leaving live state
        if (stateId !== 'live-state') {
            voiceController.stop();
        }

        const mainScroll = document.getElementById('main-scroll-area');
        if (mainScroll) mainScroll.scrollTop = 0;
    },

    setLoading(message) {
        const msgEl = document.getElementById('loading-message');
        if (msgEl) msgEl.textContent = message || 'Processing...';
        this.switchState('loading-state');
    },

    /**
     * Restore session state across browser refreshes so countdown and interview
     * resume seamlessly from the persisted deadline.
     */
    checkRestoredSession() {
        const raw = sessionStorage.getItem(this.SESSION_KEY);
        if (!raw) return;

        try {
            const data = JSON.parse(raw);
            if (!data || !data.sessionId || !data.deadlineAt) {
                sessionStorage.removeItem(this.SESSION_KEY);
                return;
            }

            const deadlineMs = typeof data.deadlineAt === 'string'
                ? Date.parse(data.deadlineAt)
                : NaN;
            if (!Number.isFinite(deadlineMs)) {
                sessionStorage.removeItem(this.SESSION_KEY);
                const timerDisplay = document.getElementById('timer-display');
                if (timerDisplay) timerDisplay.textContent = 'Unavailable';
                utils.showNotification(
                    'The saved interview has an invalid deadline. Please start a new interview.',
                    'error'
                );
                return;
            }

            this.currentSessionId = data.sessionId;
            this.totalQuestions = data.totalQuestions || 10;
            this.currentQuestionNumber = data.questionNumber || 1;
            this._timerExpiredHandled = false;

            if (Date.now() >= deadlineMs) {
                // Expired while user was away — trigger timeout finalization
                this.renderQuestion(data.questionNumber, data.questionText, data.category);
                this.switchState('live-state');
                this.handleTimerExpired();
                return;
            }

            // Still active — render question and resume countdown
            this.renderQuestion(data.questionNumber, data.questionText, data.category);
            timerController.start(data.deadlineAt, () => this.handleTimerExpired());
            this.switchState('live-state');
            utils.showNotification('Resumed live interview session.', 'info');
        } catch (e) {
            console.error('Failed to restore interview session:', e);
            sessionStorage.removeItem(this.SESSION_KEY);
        }
    },

    _saveActiveSession(deadlineAt, questionNumber, questionText, category) {
        const sessionData = {
            sessionId: this.currentSessionId,
            totalQuestions: this.totalQuestions,
            currentQuestionNumber: questionNumber,
            questionNumber,
            questionText,
            category,
            deadlineAt
        };
        sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(sessionData));
    },

    async handleStartInterview(e) {
        e.preventDefault();

        const form = e.target;
        const btn = document.getElementById('start-btn');
        const originalHtml = btn.innerHTML;

        const formData = new FormData(form);
        const durationRaw = Number(formData.get('duration_minutes'));
        const payload = {
            target_role: formData.get('target_role').trim(),
            interview_type: formData.get('interview_type'),
            difficulty: formData.get('difficulty'),
            total_questions: Number(formData.get('total_questions')),
            duration_minutes: durationRaw,
        };

        const title = formData.get('title').trim();
        payload.title = title || `${payload.target_role} Interview`;

        // Client-side validation
        if (
            !payload.target_role ||
            !payload.interview_type ||
            !payload.difficulty ||
            !Number.isFinite(payload.total_questions) ||
            payload.total_questions < 1 || payload.total_questions > 20
        ) {
            utils.showNotification('Please fill all required fields correctly (1-20 questions).', 'warning');
            return;
        }
        if (!Number.isFinite(payload.duration_minutes) || payload.duration_minutes < 1 || payload.duration_minutes > 60 || !Number.isInteger(payload.duration_minutes)) {
            utils.showNotification('Duration must be a whole number between 1 and 60 minutes.', 'warning');
            return;
        }

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Starting...';
            this.setLoading('Preparing your mock interview...');

            const response = await api.startInterview(payload);

            const deadlineMs = response && typeof response.deadline_at === 'string'
                ? Date.parse(response.deadline_at)
                : NaN;
            if (!Number.isFinite(deadlineMs)) {
                timerController.clear();
                const timerDisplay = document.getElementById('timer-display');
                if (timerDisplay) timerDisplay.textContent = 'Unavailable';
                throw new Error(
                    'The server did not return a valid deadline_at timestamp. Please try again.'
                );
            }

            this.currentSessionId = response.session_id;
            this.totalQuestions = payload.total_questions;
            this._timerExpiredHandled = false;

            // Clear any stale timer from a previous session
            timerController.clear();

            this._saveActiveSession(
                response.deadline_at,
                response.question_number,
                response.question,
                response.category
            );

            this.renderQuestion(
                response.question_number,
                response.question,
                response.category
            );

            this.switchState('live-state');

            // Start the countdown AFTER switching to live-state so the
            // timer-display element is visible when _tick() first fires.
            console.log('[Timer] Starting countdown to deadline:', response.deadline_at);
            timerController.start(response.deadline_at, () => this.handleTimerExpired());
            console.log('[Timer] timer-display after start:', document.getElementById('timer-display')?.textContent);

            utils.showNotification('Interview started. Good luck!', 'success');

        } catch (error) {
            console.error("Error starting interview:", error);
            timerController.clear();
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

        const percentage = Math.min(100, Math.max(0, (number / this.totalQuestions) * 100));
        document.getElementById('progress-fill').style.width = `${percentage}%`;

        document.getElementById('current-question-text').textContent = questionText;

        const textarea = document.getElementById('answer-input');
        if (textarea) {
            textarea.value = '';
            textarea.style.height = '';
        }

        // Re-enable controls for next question
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) submitBtn.disabled = false;
        if (textarea) textarea.disabled = false;
        voiceController.enable();
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
            textarea.disabled = true;
            voiceController.disable();
            this.setLoading('Evaluating your response...');

            const response = await api.submitInterviewAnswer(this.currentSessionId, answer);

            if (response.completed) {
                timerController.clear();
                sessionStorage.removeItem(this.SESSION_KEY);
                await this.fetchAndRenderReport();
            } else if (response.next_question) {
                // Update persisted session for the next question
                const saved = JSON.parse(sessionStorage.getItem(this.SESSION_KEY) || '{}');
                if (saved.deadlineAt) {
                    this._saveActiveSession(
                        saved.deadlineAt,
                        response.next_question.question_order,
                        response.next_question.question,
                        null
                    );
                }

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

            // If deadline exceeded — trigger timeout flow immediately
            const msg = error.message || '';
            if (msg.includes('time has expired') || msg.includes('expired') || msg.includes('409')) {
                utils.showNotification('Time expired. Generating partial report…', 'warning');
                await this.handleTimerExpired();
                return;
            }

            utils.showNotification(msg || 'Failed to submit answer.', 'error');
            this.switchState('live-state');
        } finally {
            btn.disabled = false;
            textarea.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    /**
     * Called when the countdown reaches 0 OR when the backend rejects
     * an answer because the deadline passed. Idempotent — safe to call
     * multiple times (backend is also idempotent).
     */
    async handleTimerExpired() {
        if (this._timerExpiredHandled) return;
        this._timerExpiredHandled = true;

        timerController.clear();
        voiceController.disable();
        sessionStorage.removeItem(this.SESSION_KEY);

        // Disable answer submission
        const submitBtn = document.getElementById('submit-answer-btn');
        const textarea = document.getElementById('answer-input');
        if (submitBtn) submitBtn.disabled = true;
        if (textarea) textarea.disabled = true;

        this.setLoading('Time is up. Generating your partial report…');

        try {
            await api.finalizeInterviewTimeout(this.currentSessionId);
            await this.fetchAndRenderReport(true /* isPartial */);
        } catch (error) {
            console.error("Error finalizing timeout:", error);
            utils.showNotification(
                error.message || 'Unable to generate partial report. Please refresh the page.',
                'error'
            );
        }
    },

    async fetchAndRenderReport(isPartial = false) {
        this.setLoading('Loading your interview report…');
        try {
            const report = await api.getInterviewReport(this.currentSessionId);

            // Use backend's authoritative is_partial flag
            const partial = report.is_partial ?? isPartial;

            // Clear session storage on report display
            sessionStorage.removeItem(this.SESSION_KEY);
            timerController.clear();

            // Title and partial badge
            const titleEl = document.getElementById('report-title');
            if (titleEl) {
                titleEl.textContent = partial ? 'Interview Report (Partial)' : 'Interview Completed';
            }
            const badge = document.getElementById('partial-report-badge');
            if (badge) {
                if (partial) badge.classList.remove('hidden');
                else badge.classList.add('hidden');
            }

            // Score circle accent color
            const scoreCircle = document.querySelector('.score-circle');
            if (scoreCircle) {
                scoreCircle.style.borderColor = partial ? '#F59E0B' : 'var(--primary)';
            }

            const hasScore = typeof report.overall_score === 'number' && Number.isFinite(report.overall_score);
            document.getElementById('report-score').textContent = hasScore ? report.overall_score.toFixed(1) : '0.0';
            document.getElementById('report-summary').textContent = report.summary || 'No summary available.';
            document.getElementById('report-recommendations').textContent = report.recommendations || 'No recommendations.';
            document.getElementById('report-readiness').textContent = report.career_readiness || 'N/A';

            this.populateList('report-strengths', report.strengths);
            this.populateList('report-weaknesses', report.weaknesses);
            this.populateList('report-next-steps', report.next_steps);

            this.switchState('report-state');
            utils.showNotification(partial ? 'Partial report ready.' : 'Interview completed!', 'success');

        } catch (error) {
            console.error("Error fetching report:", error);
            utils.showNotification(error.message || 'Failed to load report.', 'error');
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
