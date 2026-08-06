// AI Career Mentor Logic

const mentorManager = {
    isWaiting: false,
    lastFocusedElement: null,

    async init() {
        try {
            await this.loadUIComponents();
            this.bindEvents();
            await this.loadHistory();
        } catch (error) {
            console.error("Mentor initialization failed:", error);
            utils.showNotification('Failed to initialize AI Mentor.', 'error');
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
                        nav.classList.add('px-4', 'lg:px-8');
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
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const chatForm = document.getElementById('chat-form');

        // Textarea auto-resize and Enter key handling
        if (chatInput) {
            chatInput.addEventListener('input', () => {
                chatInput.style.height = 'auto';
                chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
                sendBtn.disabled = chatInput.value.trim().length === 0 || this.isWaiting;
            });

            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!sendBtn.disabled) {
                        chatForm.dispatchEvent(new Event('submit'));
                    }
                }
            });
        }

        // Form submission
        if (chatForm) {
            chatForm.addEventListener('submit', this.handleSendMessage.bind(this));
        }

        // Suggestions empty state
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (chatInput && !this.isWaiting) {
                    chatInput.value = e.target.textContent;
                    chatInput.dispatchEvent(new Event('input'));
                    chatInput.focus();
                }
            });
        });

        // Clear History
        document.getElementById('clear-chat-btn')?.addEventListener('click', () => {
            this.openModal('clear-modal');
        });

        document.getElementById('confirm-clear-btn')?.addEventListener('click', this.handleClearHistory.bind(this));

        // Modals closing
        document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal-overlay');
                if (modal) this.closeModal(modal.id);
            });
        });

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

    // A lightweight parser to handle potential markdown safely without assuming 100% markdown compliance
    formatMessageText(text) {
        // First escape HTML to prevent XSS
        let formatted = this.escapeHTML(text);
        
        // Code Blocks ```code```
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code `code`
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold **text**
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Bullet Lists (- item or * item)
        // Convert to pseudo-list rendering securely via replace
        formatted = formatted.replace(/(?:^|\n)[-*]\s+(.+)/g, '<br>&bull; $1');

        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        // Cleanup multiple line breaks at start/end or consecutive
        formatted = formatted.replace(/^(?:<br>)+/, '').replace(/(?:<br>)+$/, '');
        
        return formatted;
    },

    scrollToBottom(force = false) {
        const historyArea = document.getElementById('chat-history');
        if (!historyArea) return;
        
        // Only scroll if we are near bottom, or forced
        const threshold = 150; 
        const isNearBottom = historyArea.scrollHeight - historyArea.scrollTop - historyArea.clientHeight < threshold;
        
        if (isNearBottom || force) {
            historyArea.scrollTo({
                top: historyArea.scrollHeight,
                behavior: 'smooth'
            });
        }
    },

    async loadHistory() {
        const loading = document.getElementById('chat-loading');
        const emptyState = document.getElementById('chat-empty-state');
        const container = document.getElementById('messages-container');
        const clearBtn = document.getElementById('clear-chat-btn');

        try {
            loading.classList.remove('hidden');
            emptyState.classList.add('hidden');
            container.innerHTML = '';

            const response = await api.getChatHistory();
            const messages = response.messages || [];

            loading.classList.add('hidden');

            if (messages.length === 0) {
                emptyState.classList.remove('hidden');
                clearBtn.classList.add('hidden');
            } else {
                emptyState.classList.add('hidden');
                clearBtn.classList.remove('hidden');
                
                messages.forEach(msg => {
                    this.appendMessage(msg.role, msg.message, msg.created_at);
                });
                
                // Jump to bottom immediately on load
                const historyArea = document.getElementById('chat-history');
                if (historyArea) {
                    historyArea.scrollTop = historyArea.scrollHeight;
                }
            }
        } catch (error) {
            console.error("Error loading chat history:", error);
            loading.classList.add('hidden');
            emptyState.classList.remove('hidden');
            utils.showNotification('Failed to load conversation history.', 'error');
        }
    },

    appendMessage(role, text, createdAt = null) {
        const container = document.getElementById('messages-container');
        if (!container) return;
        
        const safeRole = this.escapeHTML(role).toLowerCase();
        // Ignore system messages from visual rendering unless required
        if (safeRole === 'system') return;
        
        const isUser = safeRole === 'user';
        const formattedText = this.formatMessageText(text);
        
        let metaHtml = '';
        if (createdAt) {
            const time = new Date(createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            metaHtml = `<div class="message-meta">${time}</div>`;
        }

        const avatarIcon = isUser ? 'fa-user' : 'fa-robot';
        
        const msgHtml = `
            <div class="chat-message ${isUser ? 'user' : 'assistant'}">
                <div class="chat-avatar" aria-hidden="true">
                    <i class="fa-solid ${avatarIcon}"></i>
                </div>
                <div class="flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-full min-w-0">
                    <div class="chat-bubble">
                        ${formattedText}
                    </div>
                    ${metaHtml}
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', msgHtml);
    },

    async handleSendMessage(e) {
        e.preventDefault();
        if (this.isWaiting) return;

        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        const sendBtn = document.getElementById('send-btn');
        const emptyState = document.getElementById('chat-empty-state');
        const typingIndicator = document.getElementById('typing-indicator');
        const clearBtn = document.getElementById('clear-chat-btn');

        if (!text) return;

        // Optimistic UI updates
        this.isWaiting = true;
        input.value = '';
        input.style.height = 'auto'; // Reset size
        sendBtn.disabled = true;
        emptyState.classList.add('hidden');
        clearBtn.classList.remove('hidden');

        // Append user message instantly
        this.appendMessage('user', text, new Date().toISOString());
        this.scrollToBottom(true);

        // Show typing indicator
        typingIndicator.classList.remove('hidden');
        this.scrollToBottom(true);

        try {
            // Post to backend API
            const response = await api.sendChatMessage(text);
            
            // Backend returns ChatResponse: role, message
            typingIndicator.classList.add('hidden');
            this.appendMessage(response.role || 'assistant', response.message, new Date().toISOString());
            this.scrollToBottom(true);

        } catch (error) {
            console.error("Error sending message:", error);
            typingIndicator.classList.add('hidden');
            this.appendMessage('system', 'Sorry, I encountered an error communicating with the server. Please try again.');
            this.scrollToBottom(true);
            
            // Restore input for retry
            input.value = text;
            input.dispatchEvent(new Event('input'));
        } finally {
            this.isWaiting = false;
            if (input.value.trim().length > 0) {
                sendBtn.disabled = false;
            }
            input.focus();
        }
    },

    async handleClearHistory() {
        const btn = document.getElementById('confirm-clear-btn');
        const originalHtml = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Clearing...';
            
            await api.deleteChatHistory();
            
            this.closeModal('clear-modal');
            utils.showNotification('Conversation cleared.', 'success');
            
            // Wipe UI and show empty state
            document.getElementById('messages-container').innerHTML = '';
            document.getElementById('chat-empty-state').classList.remove('hidden');
            document.getElementById('clear-chat-btn').classList.add('hidden');
            
        } catch (error) {
            console.error("Error clearing chat history:", error);
            utils.showNotification(error.message || 'Failed to clear history.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
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
        if (this.lastFocusedElement) {
            this.lastFocusedElement.focus();
            this.lastFocusedElement = null;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    mentorManager.init();
});
