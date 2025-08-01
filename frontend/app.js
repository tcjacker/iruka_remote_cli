// 应用配置
const CONFIG = {
    API_BASE_URL: 'http://localhost:8081',
    TOAST_DURATION: 5000,
    CHAT_SCROLL_DELAY: 100
};

// 应用状态
const AppState = {
    currentEnvironment: null,
    environments: [],
    isConnected: false,
    chatHistory: []
};

// DOM 元素引用
const Elements = {
    createEnvBtn: document.getElementById('createEnvBtn'),
    refreshEnvBtn: document.getElementById('refreshEnvBtn'),
    environmentList: document.getElementById('environmentList'),
    currentEnvId: document.getElementById('currentEnvId'),
    configSection: document.getElementById('configSection'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    gitRepoUrl: document.getElementById('gitRepoUrl'),
    gitPrivateKey: document.getElementById('gitPrivateKey'),
    gitTargetDir: document.getElementById('gitTargetDir'),
    cloneRepoBtn: document.getElementById('cloneRepoBtn'),
    geminiApiKey: document.getElementById('geminiApiKey'),
    configureGeminiBtn: document.getElementById('configureGeminiBtn'),
    geminiStatus: document.getElementById('geminiStatus'),
    chatSection: document.getElementById('chatSection'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendMessageBtn: document.getElementById('sendMessageBtn'),
    clearChatBtn: document.getElementById('clearChatBtn'),
    sessionStatusBtn: document.getElementById('sessionStatusBtn'),
    resetSessionBtn: document.getElementById('resetSessionBtn'),
    fileSection: document.getElementById('fileSection'),
    listFilesBtn: document.getElementById('listFilesBtn'),
    executeCodeBtn: document.getElementById('executeCodeBtn'),
    fileList: document.getElementById('fileList'),
    connectionStatus: document.getElementById('connectionStatus'),
    connectionText: document.getElementById('connectionText'),
    currentTime: document.getElementById('currentTime'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    toastContainer: document.getElementById('toastContainer')
};

// 工具函数
const Utils = {
    showLoading(text = '处理中...') {
        Elements.loadingText.textContent = text;
        Elements.loadingOverlay.style.display = 'flex';
    },

    hideLoading() {
        Elements.loadingOverlay.style.display = 'none';
    },

    showToast(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getToastIcon(type);
        toast.innerHTML = `<i class="fas ${icon}"></i><span>${message}</span>`;
        
        Elements.toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), duration);
    },

    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    },

    formatTime(date = new Date()) {
        return date.toLocaleTimeString('zh-CN', {
            hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    }
};

// API 调用函数
const API = {
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },

    async createEnvironment() {
        return await this.request('/environments', { method: 'POST' });
    },

    async deleteEnvironment(envId) {
        return await this.request(`/environments/${envId}`, { method: 'DELETE' });
    },

    async healthCheck() {
        return await this.request('/health');
    },

    async configureGemini(envId, apiKey) {
        return await this.request(`/environments/${envId}/gemini/configure`, {
            method: 'POST',
            body: JSON.stringify({ api_key: apiKey })
        });
    },

    async sendGeminiMessage(envId, prompt, useSession = true) {
        const endpoint = useSession ? 'session' : 'chat';
        return await this.request(`/environments/${envId}/gemini/${endpoint}`, {
            method: 'POST',
            body: JSON.stringify({ prompt })
        });
    },

    async getGeminiSessionStatus(envId) {
        return await this.request(`/environments/${envId}/gemini/session/status`);
    },

    async resetGeminiSession(envId) {
        return await this.request(`/environments/${envId}/gemini/session/reset`, { method: 'POST' });
    },

    async cloneRepository(envId, repoUrl, targetDir = './workspace') {
        return await this.request(`/environments/${envId}/git/clone`, {
            method: 'POST',
            body: JSON.stringify({ repo_url: repoUrl, target_dir: targetDir })
        });
    },

    async listFiles(envId, dir = './workspace') {
        return await this.request(`/environments/${envId}/files/list?dir=${encodeURIComponent(dir)}`);
    },

    async readFile(envId, path, dir = './workspace') {
        return await this.request(`/environments/${envId}/files/read?path=${encodeURIComponent(path)}&dir=${encodeURIComponent(dir)}`);
    },

    async executeCommand(envId, command) {
        return await this.request(`/environments/${envId}/execute`, {
            method: 'POST',
            body: JSON.stringify({ command })
        });
    }
};

// 环境管理功能
const EnvironmentManager = {
    async createEnvironment() {
        try {
            Utils.showLoading('创建环境中...');
            const result = await API.createEnvironment();
            
            const environment = {
                id: result.env_id,
                port: result.port,
                status: 'running',
                createdAt: new Date()
            };
            
            AppState.environments.push(environment);
            this.renderEnvironments();
            Utils.showToast('环境创建成功！', 'success');
            
        } catch (error) {
            Utils.showToast(`创建环境失败: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    selectEnvironment(envId) {
        AppState.currentEnvironment = AppState.environments.find(env => env.id === envId);
        
        if (AppState.currentEnvironment) {
            Elements.currentEnvId.textContent = envId;
            Elements.configSection.style.display = 'block';
            Elements.chatSection.style.display = 'block';
            Elements.fileSection.style.display = 'block';
            
            this.renderEnvironments();
            Utils.showToast('环境已选择', 'success');
        }
    },

    async deleteEnvironment(envId) {
        if (!confirm('确定要删除这个环境吗？')) return;
        
        try {
            Utils.showLoading('删除环境中...');
            await API.deleteEnvironment(envId);
            
            AppState.environments = AppState.environments.filter(env => env.id !== envId);
            
            if (AppState.currentEnvironment && AppState.currentEnvironment.id === envId) {
                AppState.currentEnvironment = null;
                Elements.currentEnvId.textContent = '未选择环境';
                Elements.configSection.style.display = 'none';
                Elements.chatSection.style.display = 'none';
                Elements.fileSection.style.display = 'none';
            }
            
            this.renderEnvironments();
            Utils.showToast('环境删除成功', 'success');
            
        } catch (error) {
            Utils.showToast(`删除环境失败: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    renderEnvironments() {
        if (AppState.environments.length === 0) {
            Elements.environmentList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-box-open"></i>
                    <p>暂无环境，点击"创建新环境"开始</p>
                </div>
            `;
            return;
        }

        Elements.environmentList.innerHTML = AppState.environments.map(env => `
            <div class="environment-item ${AppState.currentEnvironment?.id === env.id ? 'active' : ''}" 
                 data-env-id="${env.id}">
                <div class="environment-header">
                    <div class="environment-id">${env.id}</div>
                    <div class="environment-status">
                        <div class="status-dot ${env.status === 'running' ? '' : 'error'}"></div>
                        <span>${env.status === 'running' ? '运行中' : '已停止'}</span>
                    </div>
                </div>
                <div class="environment-info">
                    <small>端口: ${env.port} | 创建时间: ${Utils.formatTime(env.createdAt)}</small>
                </div>
                <div class="environment-actions">
                    <button class="btn btn-sm btn-primary select-env-btn" data-env-id="${env.id}">
                        <i class="fas fa-mouse-pointer"></i> 选择
                    </button>
                    <button class="btn btn-sm btn-danger delete-env-btn" data-env-id="${env.id}">
                        <i class="fas fa-trash"></i> 删除
                    </button>
                </div>
            </div>
        `).join('');

        // 绑定事件
        Elements.environmentList.querySelectorAll('.select-env-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectEnvironment(btn.dataset.envId);
            });
        });

        Elements.environmentList.querySelectorAll('.delete-env-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteEnvironment(btn.dataset.envId);
            });
        });
    },

    async refreshEnvironments() {
        try {
            await API.healthCheck();
            AppState.isConnected = true;
            this.updateConnectionStatus();
        } catch (error) {
            AppState.isConnected = false;
            this.updateConnectionStatus();
            Utils.showToast('无法连接到服务器', 'error');
        }
    },

    updateConnectionStatus() {
        if (AppState.isConnected) {
            Elements.connectionStatus.className = 'fas fa-circle connected';
            Elements.connectionText.textContent = '已连接';
        } else {
            Elements.connectionStatus.className = 'fas fa-circle';
            Elements.connectionText.textContent = '未连接';
        }
    }
};

// Git 配置功能
const GitManager = {
    async cloneRepository() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        const repoUrl = Elements.gitRepoUrl.value.trim();
        const targetDir = Elements.gitTargetDir.value.trim() || './workspace';

        if (!repoUrl) {
            Utils.showToast('请输入 Git 仓库地址', 'warning');
            return;
        }

        try {
            Utils.showLoading('克隆仓库中...');
            
            const privateKey = Elements.gitPrivateKey.value.trim();
            if (privateKey) {
                console.log('SSH Private Key provided:', privateKey.substring(0, 50) + '...');
            }

            await API.cloneRepository(AppState.currentEnvironment.id, repoUrl, targetDir);
            Utils.showToast('仓库克隆成功！', 'success');
            FileManager.listFiles();

        } catch (error) {
            Utils.showToast(`克隆仓库失败: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    }
};

// Gemini 配置功能
const GeminiManager = {
    async configureGemini() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        const apiKey = Elements.geminiApiKey.value.trim();
        if (!apiKey) {
            Utils.showToast('请输入 Gemini API Key', 'warning');
            return;
        }

        try {
            Utils.showLoading('配置 Gemini API...');
            
            await API.configureGemini(AppState.currentEnvironment.id, apiKey);
            
            Elements.geminiStatus.style.display = 'flex';
            Elements.geminiStatus.className = 'status-indicator success';
            Elements.geminiStatus.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Gemini API 配置成功</span>
            `;

            Utils.showToast('Gemini API 配置成功！', 'success');

        } catch (error) {
            Elements.geminiStatus.style.display = 'flex';
            Elements.geminiStatus.className = 'status-indicator error';
            Elements.geminiStatus.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <span>配置失败: ${error.message}</span>
            `;
            
            Utils.showToast(`Gemini API 配置失败: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    async sendMessage() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        const message = Elements.chatInput.value.trim();
        if (!message) {
            Utils.showToast('请输入消息内容', 'warning');
            return;
        }

        try {
            this.addMessage('user', message);
            Elements.chatInput.value = '';

            const result = await API.sendGeminiMessage(AppState.currentEnvironment.id, message, true);
            this.addMessage('assistant', result.response || result.output || '无回复');

        } catch (error) {
            this.addMessage('system', `错误: ${error.message}`);
            Utils.showToast(`发送消息失败: ${error.message}`, 'error');
        }
    },

    addMessage(role, content) {
        const welcomeMessage = Elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const icons = { user: 'fa-user', assistant: 'fa-robot', system: 'fa-exclamation-triangle' };
        const names = { user: '你', assistant: 'Gemini', system: '系统' };

        const formattedContent = this.formatMessageContent(content);

        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas ${icons[role]}"></i>
                <span>${names[role]}</span>
                <small>${Utils.formatTime()}</small>
            </div>
            <div class="message-content">${formattedContent}</div>
        `;

        Elements.chatMessages.appendChild(messageDiv);
        
        setTimeout(() => {
            Elements.chatMessages.scrollTop = Elements.chatMessages.scrollHeight;
        }, CONFIG.CHAT_SCROLL_DELAY);

        AppState.chatHistory.push({ role, content, timestamp: new Date() });
    },

    formatMessageContent(content) {
        // 检查是否包含 CLI 装饰性字符（Unicode box drawing characters）
        const hasCliDecorations = /[\u2500-\u257F\u2580-\u259F]/.test(content);
        
        if (hasCliDecorations) {
            // CLI 风格渲染：保持原始格式和装饰字符
            return this.renderCliContent(content);
        } else {
            // 标准 Markdown 渲染
            return this.renderMarkdownContent(content);
        }
    },

    renderCliContent(content) {
        // 为 CLI 输出创建专门的渲染容器
        const lines = content.split('\n');
        let htmlContent = '<div class="cli-output">';
        
        lines.forEach(line => {
            // 保持原始的空格和 Unicode 字符
            const escapedLine = line
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/ /g, '&nbsp;'); // 保持空格
            
            htmlContent += `<div class="cli-line">${escapedLine}</div>`;
        });
        
        htmlContent += '</div>';
        return htmlContent;
    },

    renderMarkdownContent(content) {
        // 处理代码块
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || 'text';
            return `<pre><code class="language-${language}">${code.trim()}</code></pre>`;
        });

        // 处理行内代码
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // 处理换行
        content = content.replace(/\n/g, '<br>');

        return content;
    },

    clearChat() {
        Elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-robot"></i>
                <p>欢迎使用 Gemini CLI！你可以在这里与 AI 助手交互，生成代码、获取帮助等。</p>
            </div>
        `;
        AppState.chatHistory = [];
        Utils.showToast('聊天记录已清空', 'info');
    },

    async getSessionStatus() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        try {
            const status = await API.getGeminiSessionStatus(AppState.currentEnvironment.id);
            const statusText = status.active ? '活跃' : '非活跃';
            const persistentText = status.persistent ? '持久' : '临时';
            Utils.showToast(`会话状态: ${statusText}, ${persistentText}`, 'info');

        } catch (error) {
            Utils.showToast(`获取会话状态失败: ${error.message}`, 'error');
        }
    },

    async resetSession() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        if (!confirm('确定要重置 Gemini 会话吗？这将清除所有对话历史。')) {
            return;
        }

        try {
            Utils.showLoading('重置会话中...');
            await API.resetGeminiSession(AppState.currentEnvironment.id);
            this.addMessage('system', '会话已重置，对话历史已清除');
            Utils.showToast('会话重置成功', 'success');

        } catch (error) {
            Utils.showToast(`重置会话失败: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    },

    async startInteractiveSession() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }
        
        try {
            // 在新窗口中打开交互式 CLI 页面
            const interactiveUrl = `interactive.html?env=${encodeURIComponent(AppState.currentEnvironment.id)}`;
            const interactiveWindow = window.open(
                interactiveUrl,
                'gemini-interactive',
                'width=1200,height=800,scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no'
            );
            
            if (!interactiveWindow) {
                throw new Error('无法打开新窗口，请检查浏览器弹窗设置');
            }
            
            // 显示成功消息
            Utils.showToast('交互式 Gemini CLI 会话已在新窗口中打开', 'success');
            
            // 记录交互式会话状态
            AppState.interactiveSession = {
                active: true,
                envId: AppState.currentEnvironment.id,
                window: interactiveWindow
            };
            
            // 监听窗口关闭事件
            const checkClosed = setInterval(() => {
                if (interactiveWindow.closed) {
                    clearInterval(checkClosed);
                    this.stopInteractiveSession();
                }
            }, 1000);
            
        } catch (error) {
            console.error('启动交互式会话失败:', error);
            Utils.showToast(`启动交互式会话失败: ${error.message}`, 'error');
        }
    },

    stopInteractiveSession() {
        if (AppState.interactiveSession) {
            if (AppState.interactiveSession.window && !AppState.interactiveSession.window.closed) {
                AppState.interactiveSession.window.close();
            }
            AppState.interactiveSession = null;
            Utils.showToast('交互式会话已结束', 'info');
        }
    }
};

// 文件管理功能
const FileManager = {
    async listFiles() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        try {
            const result = await API.listFiles(AppState.currentEnvironment.id);
            this.renderFileList(result.files || []);

        } catch (error) {
            Utils.showToast(`获取文件列表失败: ${error.message}`, 'error');
        }
    },

    renderFileList(files) {
        if (files.length === 0) {
            Elements.fileList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p>工作区为空</p>
                </div>
            `;
            return;
        }

        Elements.fileList.innerHTML = files.map(file => `
            <div class="file-item" data-file-path="${file}">
                <i class="fas ${this.getFileIcon(file)} file-icon"></i>
                <span class="file-name">${file}</span>
            </div>
        `).join('');

        Elements.fileList.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', () => {
                this.viewFile(item.dataset.filePath);
            });
        });
    },

    getFileIcon(filename) {
        const ext = filename.split('.').pop()?.toLowerCase();
        const iconMap = {
            'py': 'fa-file-code', 'js': 'fa-file-code', 'html': 'fa-file-code',
            'css': 'fa-file-code', 'json': 'fa-file-code', 'md': 'fa-file-alt',
            'txt': 'fa-file-alt', 'yml': 'fa-file-alt', 'yaml': 'fa-file-alt',
            'png': 'fa-file-image', 'jpg': 'fa-file-image', 'jpeg': 'fa-file-image'
        };
        return iconMap[ext] || 'fa-file';
    },

    async viewFile(filePath) {
        if (!AppState.currentEnvironment) return;

        try {
            const result = await API.readFile(AppState.currentEnvironment.id, filePath);
            GeminiManager.addMessage('system', `文件: ${filePath}\n\`\`\`\n${result.content}\n\`\`\``);

        } catch (error) {
            Utils.showToast(`读取文件失败: ${error.message}`, 'error');
        }
    },

    async executeCode() {
        if (!AppState.currentEnvironment) {
            Utils.showToast('请先选择一个环境', 'warning');
            return;
        }

        const command = prompt('请输入要执行的命令:', 'python main.py');
        if (!command) return;

        try {
            Utils.showLoading('执行代码中...');
            
            const result = await API.executeCommand(AppState.currentEnvironment.id, command);
            
            const output = result.stdout || result.output || '无输出';
            const error = result.stderr || result.error;
            
            let message = `执行命令: ${command}\n\n`;
            if (output) message += `输出:\n\`\`\`\n${output}\n\`\`\`\n`;
            if (error) message += `错误:\n\`\`\`\n${error}\n\`\`\``;

            GeminiManager.addMessage('system', message);
            
            if (result.returncode === 0) {
                Utils.showToast('代码执行成功', 'success');
            } else {
                Utils.showToast('代码执行出现错误', 'warning');
            }

        } catch (error) {
            Utils.showToast(`执行代码失败: ${error.message}`, 'error');
        } finally {
            Utils.hideLoading();
        }
    }
};

// UI 控制功能
const UIController = {
    initTabs() {
        Elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                this.switchTab(tabId);
            });
        });
    },

    switchTab(tabId) {
        Elements.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        Elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}Config`);
        });
    },

    updateTime() {
        Elements.currentTime.textContent = Utils.formatTime();
    },

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                if (document.activeElement === Elements.chatInput) {
                    GeminiManager.sendMessage();
                }
            }
            
            if (e.key === 'Escape') {
                Utils.hideLoading();
            }
        });
    }
};

// 应用初始化
const App = {
    init() {
        this.bindEvents();
        this.initUI();
        this.startPeriodicTasks();
        EnvironmentManager.refreshEnvironments();
        console.log('🚀 Gemini CLI Docker 管理界面已启动');
    },

    bindEvents() {
        Elements.createEnvBtn.addEventListener('click', () => EnvironmentManager.createEnvironment());
        Elements.refreshEnvBtn.addEventListener('click', () => EnvironmentManager.refreshEnvironments());
        Elements.cloneRepoBtn.addEventListener('click', () => GitManager.cloneRepository());
        Elements.configureGeminiBtn.addEventListener('click', () => GeminiManager.configureGemini());
        Elements.sendMessageBtn.addEventListener('click', () => GeminiManager.sendMessage());
        Elements.clearChatBtn.addEventListener('click', () => GeminiManager.clearChat());
        Elements.sessionStatusBtn.addEventListener('click', () => GeminiManager.getSessionStatus());
        Elements.resetSessionBtn.addEventListener('click', () => GeminiManager.resetSession());
        Elements.listFilesBtn.addEventListener('click', () => FileManager.listFiles());
        Elements.executeCodeBtn.addEventListener('click', () => FileManager.executeCode());
        
        // 交互式会话按钮
        const startInteractiveBtn = document.getElementById('startInteractiveBtn');
        const stopInteractiveBtn = document.getElementById('stopInteractiveBtn');
        
        if (startInteractiveBtn) {
            startInteractiveBtn.addEventListener('click', () => GeminiManager.startInteractiveSession());
        }
        
        if (stopInteractiveBtn) {
            stopInteractiveBtn.addEventListener('click', () => GeminiManager.stopInteractiveSession());
        }
    },

    initUI() {
        UIController.initTabs();
        UIController.initKeyboardShortcuts();
    },

    startPeriodicTasks() {
        setInterval(() => {
            UIController.updateTime();
        }, 1000);
    }
};

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
