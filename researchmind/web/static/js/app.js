// ResearchMind AI - Frontend Reactive Controller

let state = {
  currentUser: null,
  activePaper: null,
  activeAnalysis: null,
  papers: [],
  activeTab: 'summary',
  currentMode: 'analysis', // 'analysis' or 'compare'
  chatHistory: [],
  isAnalyzing: false,
};

// DOM References
const elements = {
  modelSelect: document.getElementById('model-select'),
  btnSettings: document.getElementById('btn-settings'),
  apiStatusDot: document.getElementById('api-status-dot'),
  apiStatusText: document.getElementById('api-status-text'),
  btnNewPaper: document.getElementById('btn-new-paper'),
  paperCountBadge: document.getElementById('paper-count-badge'),
  paperListContainer: document.getElementById('paper-list-container'),
  searchPapers: document.getElementById('search-papers'),

  // Auth elements
  authUnauthenticated: document.getElementById('auth-unauthenticated'),
  authAuthenticated: document.getElementById('auth-authenticated'),
  btnOpenSignin: document.getElementById('btn-open-signin'),
  btnOpenSignup: document.getElementById('btn-open-signup'),
  btnUserProfile: document.getElementById('btn-user-profile'),
  userAvatarInitials: document.getElementById('user-avatar-initials'),
  userDisplayName: document.getElementById('user-display-name'),
  userDropdownName: document.getElementById('user-dropdown-name'),
  userDropdownEmail: document.getElementById('user-dropdown-email'),
  btnSignout: document.getElementById('btn-signout'),

  authModal: document.getElementById('auth-modal'),
  closeAuthModal: document.getElementById('close-auth-modal'),
  authTabSignin: document.getElementById('auth-tab-signin'),
  authTabSignup: document.getElementById('auth-tab-signup'),
  authAlert: document.getElementById('auth-alert'),
  formSignin: document.getElementById('form-signin'),
  signinIdentifier: document.getElementById('signin-identifier'),
  signinPassword: document.getElementById('signin-password'),
  btnSubmitSignin: document.getElementById('btn-submit-signin'),
  formSignup: document.getElementById('form-signup'),
  signupUsername: document.getElementById('signup-username'),
  signupEmail: document.getElementById('signup-email'),
  signupPassword: document.getElementById('signup-password'),
  signupConfirmPassword: document.getElementById('signup-confirm-password'),
  btnSubmitSignup: document.getElementById('btn-submit-signup'),
  btnContinueGuest: document.getElementById('btn-continue-guest'),
  
  modeAnalysisBtn: document.getElementById('mode-analysis-btn'),
  modeCompareBtn: document.getElementById('mode-compare-btn'),
  
  viewIngestion: document.getElementById('view-ingestion'),
  viewAnalysis: document.getElementById('view-analysis'),
  viewCompare: document.getElementById('view-compare'),
  
  tabBtnArxiv: document.getElementById('tab-btn-arxiv'),
  tabBtnPdf: document.getElementById('tab-btn-pdf'),
  formArxiv: document.getElementById('form-arxiv'),
  formPdf: document.getElementById('form-pdf'),
  inputArxiv: document.getElementById('input-arxiv'),
  btnFetchArxiv: document.getElementById('btn-fetch-arxiv'),
  dropzone: document.getElementById('dropzone'),
  pdfFileInput: document.getElementById('pdf-file-input'),
  ingestionLoader: document.getElementById('ingestion-loader'),
  ingestionStatusText: document.getElementById('ingestion-status-text'),
  
  bannerTitle: document.getElementById('banner-title'),
  bannerAuthors: document.getElementById('banner-authors'),
  bannerArxivBadge: document.getElementById('banner-arxiv-badge'),
  bannerPagesBadge: document.getElementById('banner-pages-badge'),
  bannerWordsBadge: document.getElementById('banner-words-badge'),
  btnRunFull: document.getElementById('btn-run-full'),
  
  progressBarContainer: document.getElementById('analysis-progress-bar-container'),
  progressMessage: document.getElementById('analysis-status-message'),
  progressPercent: document.getElementById('analysis-progress-percent'),
  progressFill: document.getElementById('analysis-progress-fill'),
  
  tabSectionContent: document.getElementById('tab-section-content'),
  sectionPlaceholder: document.getElementById('section-placeholder'),
  sectionRenderedBody: document.getElementById('section-rendered-body'),
  
  tabChatContainer: document.getElementById('tab-chat-container'),
  chatStartersBox: document.getElementById('chat-starters-box'),
  chatStartersList: document.getElementById('chat-starters-list'),
  chatThread: document.getElementById('chat-thread'),
  chatForm: document.getElementById('chat-form'),
  chatInput: document.getElementById('chat-input'),
  
  compareSelectionList: document.getElementById('compare-selection-list'),
  btnRunCompare: document.getElementById('btn-run-compare'),
  compareResultPlaceholder: document.getElementById('compare-result-placeholder'),
  compareRenderedBody: document.getElementById('compare-rendered-body'),
  
  exportMd: document.getElementById('export-md'),
  exportHtml: document.getElementById('export-html'),
  exportJson: document.getElementById('export-json'),
  
  settingsModal: document.getElementById('settings-modal'),
  closeSettings: document.getElementById('close-settings'),
  settingApiKey: document.getElementById('setting-api-key'),
  btnSaveSettings: document.getElementById('btn-save-settings'),
  btnThemeToggle: document.getElementById('btn-theme-toggle'),
  themeIcon: document.getElementById('theme-icon'),
};

// Theme Controller (Light / Dark)
function initTheme() {
  const urlParam = new URLSearchParams(window.location.search).get('theme');
  const saved = urlParam || localStorage.getItem('researchmind_theme') || 'dark';
  applyTheme(saved);
}

function applyTheme(theme) {
  const isLight = theme === 'light';
  if (isLight) {
    document.documentElement.classList.add('light-theme');
    document.body.classList.add('light-theme');
    if (elements.themeIcon) {
      elements.themeIcon.setAttribute('data-lucide', 'moon');
      elements.themeIcon.className = 'w-4 h-4 text-indigo-400';
    }
    if (elements.btnThemeToggle) {
      elements.btnThemeToggle.title = 'Switch to Dark Mode';
    }
  } else {
    document.documentElement.classList.remove('light-theme');
    document.body.classList.remove('light-theme');
    if (elements.themeIcon) {
      elements.themeIcon.setAttribute('data-lucide', 'sun');
      elements.themeIcon.className = 'w-4 h-4 text-amber-400';
    }
    if (elements.btnThemeToggle) {
      elements.btnThemeToggle.title = 'Switch to Light Mode';
    }
  }
  localStorage.setItem('researchmind_theme', theme);
  if (window.lucide) {
    lucide.createIcons();
  }
}

function toggleTheme() {
  const current = localStorage.getItem('researchmind_theme') || 'dark';
  applyTheme(current === 'light' ? 'dark' : 'light');
}

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  setupEventListeners();
  await checkCurrentUser();
  await checkConfig();
  await loadPaperLibrary();
});

// Setup All UI Event Handlers
function setupEventListeners() {
  // Theme Toggle
  if (elements.btnThemeToggle) {
    elements.btnThemeToggle.addEventListener('click', toggleTheme);
  }

  // Auth Modals & Actions
  if (elements.btnOpenSignin) {
    elements.btnOpenSignin.addEventListener('click', () => openAuthModal('signin'));
  }
  if (elements.btnOpenSignup) {
    elements.btnOpenSignup.addEventListener('click', () => openAuthModal('signup'));
  }
  if (elements.closeAuthModal) {
    elements.closeAuthModal.addEventListener('click', closeAuthModal);
  }
  if (elements.btnContinueGuest) {
    elements.btnContinueGuest.addEventListener('click', closeAuthModal);
  }
  if (elements.authTabSignin) {
    elements.authTabSignin.addEventListener('click', () => switchAuthTab('signin'));
  }
  if (elements.authTabSignup) {
    elements.authTabSignup.addEventListener('click', () => switchAuthTab('signup'));
  }
  if (elements.formSignin) {
    elements.formSignin.addEventListener('submit', handleSigninSubmit);
  }
  if (elements.formSignup) {
    elements.formSignup.addEventListener('submit', handleSignupSubmit);
  }
  if (elements.btnSignout) {
    elements.btnSignout.addEventListener('click', handleSignout);
  }

  // Navigation & Modes
  elements.btnNewPaper.addEventListener('click', showIngestionView);
  elements.modeAnalysisBtn.addEventListener('click', () => setMode('analysis'));
  elements.modeCompareBtn.addEventListener('click', () => setMode('compare'));

  // Ingestion tabs
  elements.tabBtnArxiv.addEventListener('click', () => switchIngestionTab('arxiv'));
  elements.tabBtnPdf.addEventListener('click', () => switchIngestionTab('pdf'));

  // ArXiv fetch
  elements.btnFetchArxiv.addEventListener('click', handleArxivFetch);
  elements.inputArxiv.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleArxivFetch();
  });

  // PDF Dropzone & File picker
  elements.dropzone.addEventListener('click', () => elements.pdfFileInput.click());
  elements.pdfFileInput.addEventListener('change', handleFileUpload);
  elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('border-indigo-500', 'bg-indigo-950/20');
  });
  elements.dropzone.addEventListener('dragleave', () => {
    elements.dropzone.classList.remove('border-indigo-500', 'bg-indigo-950/20');
  });
  elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('border-indigo-500', 'bg-indigo-950/20');
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  // Settings Modal
  elements.btnSettings.addEventListener('click', () => elements.settingsModal.classList.remove('hidden'));
  elements.closeSettings.addEventListener('click', () => elements.settingsModal.classList.add('hidden'));
  elements.btnSaveSettings.addEventListener('click', saveSettings);

  // Analysis tabs
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => switchSectionTab(btn.getAttribute('data-tab')));
  });

  // Run full analysis
  elements.btnRunFull.addEventListener('click', runFullAnalysis);

  // Chat form submit
  elements.chatForm.addEventListener('submit', handleChatSubmit);

  // Compare run
  elements.btnRunCompare.addEventListener('click', runComparison);

  // Search filter
  elements.searchPapers.addEventListener('input', (e) => renderPaperList(e.target.value));
}

// ==================== User Authentication Handlers ====================

async function checkCurrentUser() {
  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();
    state.currentUser = data.user || null;
    updateAuthUI();
  } catch (err) {
    console.error('Failed to check current user:', err);
  }
}

function updateAuthUI() {
  if (state.currentUser) {
    if (elements.authUnauthenticated) elements.authUnauthenticated.classList.add('hidden');
    if (elements.authAuthenticated) elements.authAuthenticated.classList.remove('hidden');
    const u = state.currentUser;
    const initial = (u.username || u.email || 'U')[0].toUpperCase();
    if (elements.userAvatarInitials) elements.userAvatarInitials.innerText = initial;
    if (elements.userDisplayName) elements.userDisplayName.innerText = u.username || u.email;
    if (elements.userDropdownName) elements.userDropdownName.innerText = u.username;
    if (elements.userDropdownEmail) elements.userDropdownEmail.innerText = u.email;
  } else {
    if (elements.authUnauthenticated) elements.authUnauthenticated.classList.remove('hidden');
    if (elements.authAuthenticated) elements.authAuthenticated.classList.add('hidden');
  }
  if (window.lucide) lucide.createIcons();
}

function openAuthModal(tab = 'signin') {
  if (!elements.authModal) return;
  elements.authModal.classList.remove('hidden');
  clearAuthAlert();
  switchAuthTab(tab);
}

function closeAuthModal() {
  if (!elements.authModal) return;
  elements.authModal.classList.add('hidden');
  clearAuthAlert();
}

function switchAuthTab(tab) {
  clearAuthAlert();
  if (tab === 'signin') {
    if (elements.authTabSignin) elements.authTabSignin.className = 'py-1.5 px-3 text-center transition font-semibold bg-white text-black';
    if (elements.authTabSignup) elements.authTabSignup.className = 'py-1.5 px-3 text-center transition font-semibold text-white/70 hover:text-white';
    if (elements.formSignin) elements.formSignin.classList.remove('hidden');
    if (elements.formSignup) elements.formSignup.classList.add('hidden');
  } else {
    if (elements.authTabSignup) elements.authTabSignup.className = 'py-1.5 px-3 text-center transition font-semibold bg-white text-black';
    if (elements.authTabSignin) elements.authTabSignin.className = 'py-1.5 px-3 text-center transition font-semibold text-white/70 hover:text-white';
    if (elements.formSignup) elements.formSignup.classList.remove('hidden');
    if (elements.formSignin) elements.formSignin.classList.add('hidden');
  }
}

function showAuthAlert(msg, isError = true) {
  if (!elements.authAlert) return;
  elements.authAlert.className = isError 
    ? 'p-3 text-xs font-mono border border-red-500/40 bg-red-950/40 text-red-300'
    : 'p-3 text-xs font-mono border border-emerald-500/40 bg-emerald-950/40 text-emerald-300';
  elements.authAlert.innerText = msg;
  elements.authAlert.classList.remove('hidden');
}

function clearAuthAlert() {
  if (!elements.authAlert) return;
  elements.authAlert.classList.add('hidden');
  elements.authAlert.innerText = '';
}

async function handleSigninSubmit(e) {
  e.preventDefault();
  const identifier = elements.signinIdentifier.value.trim();
  const password = elements.signinPassword.value;
  if (!identifier || !password) {
    showAuthAlert('Please fill in both identifier and password.');
    return;
  }

  elements.btnSubmitSignin.disabled = true;
  elements.btnSubmitSignin.innerText = 'Signing In...';

  try {
    const res = await fetch('/api/auth/signin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password }),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || 'Failed to sign in');
    }

    state.currentUser = data.user;
    updateAuthUI();
    closeAuthModal();
    elements.signinPassword.value = '';
    await loadPaperLibrary();
  } catch (err) {
    showAuthAlert(err.message);
  } finally {
    elements.btnSubmitSignin.disabled = false;
    elements.btnSubmitSignin.innerText = 'Sign In';
  }
}

async function handleSignupSubmit(e) {
  e.preventDefault();
  const username = elements.signupUsername.value.trim();
  const email = elements.signupEmail.value.trim();
  const password = elements.signupPassword.value;
  const confirmPassword = elements.signupConfirmPassword.value;

  if (password !== confirmPassword) {
    showAuthAlert('Passwords do not match. Please verify.');
    return;
  }

  elements.btnSubmitSignup.disabled = true;
  elements.btnSubmitSignup.innerText = 'Creating Account...';

  try {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || 'Failed to create account');
    }

    state.currentUser = data.user;
    updateAuthUI();
    closeAuthModal();
    elements.signupPassword.value = '';
    elements.signupConfirmPassword.value = '';
    await loadPaperLibrary();
  } catch (err) {
    showAuthAlert(err.message);
  } finally {
    elements.btnSubmitSignup.disabled = false;
    elements.btnSubmitSignup.innerText = 'Create Account';
  }
}

async function handleSignout() {
  try {
    await fetch('/api/auth/signout', { method: 'POST' });
    state.currentUser = null;
    updateAuthUI();
    showIngestionView();
    await loadPaperLibrary();
  } catch (err) {
    console.error('Failed to sign out:', err);
  }
}


// Config & API Key Check
async function checkConfig() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    if (data.api_key_configured) {
      elements.apiStatusDot.className = 'w-2 h-2 rounded-full bg-emerald-500';
      elements.apiStatusText.innerText = 'Gemini Ready';
      elements.btnSettings.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-emerald-800 bg-emerald-950/40 text-emerald-300 text-sm font-medium transition-colors';
    } else {
      elements.apiStatusDot.className = 'w-2 h-2 rounded-full bg-amber-500 animate-pulse';
      elements.apiStatusText.innerText = 'Set API Key';
      elements.btnSettings.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-amber-800 bg-amber-950/40 text-amber-300 text-sm font-medium transition-colors';
    }
    if (data.available_models && data.available_models.length > 0) {
      const currentVal = elements.modelSelect.value;
      elements.modelSelect.innerHTML = data.available_models.map((m) => `
        <option value="${m.id}" class="bg-slate-900">${m.name}${m.default ? ' (Recommended)' : ''}</option>
      `).join('');
      if (data.default_model) {
        elements.modelSelect.value = data.default_model;
      } else if (currentVal) {
        elements.modelSelect.value = currentVal;
      }
    } else if (data.default_model) {
      elements.modelSelect.value = data.default_model;
    }
  } catch (err) {
    console.error('Failed to load config:', err);
  }
}

async function saveSettings() {
  const apiKey = elements.settingApiKey.value.trim();
  const defaultModel = elements.modelSelect.value;
  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, default_model: defaultModel }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      elements.settingsModal.classList.add('hidden');
      await checkConfig();
    }
  } catch (err) {
    alert('Failed to save settings: ' + err.message);
  }
}

// Ingestion Tabs (ArXiv vs PDF)
function switchIngestionTab(tab) {
  if (tab === 'arxiv') {
    elements.tabBtnArxiv.className = 'px-5 py-2.5 text-sm font-medium border-b-2 border-indigo-500 text-indigo-400 transition';
    elements.tabBtnPdf.className = 'px-5 py-2.5 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition';
    elements.formArxiv.classList.remove('hidden');
    elements.formPdf.classList.add('hidden');
  } else {
    elements.tabBtnPdf.className = 'px-5 py-2.5 text-sm font-medium border-b-2 border-indigo-500 text-indigo-400 transition';
    elements.tabBtnArxiv.className = 'px-5 py-2.5 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition';
    elements.formPdf.classList.remove('hidden');
    elements.formArxiv.classList.add('hidden');
  }
}

window.setArxivExample = function(arxivId) {
  elements.inputArxiv.value = arxivId;
  handleArxivFetch();
};

// ArXiv Ingestion
async function handleArxivFetch() {
  const query = elements.inputArxiv.value.trim();
  if (!query) return;

  showIngestionLoading(true, `Querying arXiv & downloading PDF (${query})...`);
  try {
    const res = await fetch('/api/arxiv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    await loadPaperLibrary();
    await selectPaper(data.paper.id);
  } catch (err) {
    alert('arXiv Ingestion Failed: ' + err.message);
  } finally {
    showIngestionLoading(false);
  }
}

// File Upload Ingestion
function handleFileUpload(e) {
  if (e.target.files.length > 0) {
    uploadFile(e.target.files[0]);
  }
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  showIngestionLoading(true, `Parsing and indexing ${file.name}...`);
  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    await loadPaperLibrary();
    await selectPaper(data.paper.id);
  } catch (err) {
    alert('Upload Failed: ' + err.message);
  } finally {
    showIngestionLoading(false);
  }
}

function showIngestionLoading(show, message = '') {
  if (show) {
    elements.ingestionLoader.classList.remove('hidden');
    elements.ingestionStatusText.innerText = message;
    elements.btnFetchArxiv.disabled = true;
  } else {
    elements.ingestionLoader.classList.add('hidden');
    elements.btnFetchArxiv.disabled = false;
  }
}

// Paper Library Operations
async function loadPaperLibrary() {
  try {
    const res = await fetch('/api/papers');
    const data = await res.json();
    state.papers = data.papers || [];
    elements.paperCountBadge.innerText = state.papers.length;
    renderPaperList();
    renderCompareSelection();
  } catch (err) {
    console.error('Failed to load paper library:', err);
  }
}

function renderPaperList(filterText = '') {
  const container = elements.paperListContainer;
  const filtered = state.papers.filter((p) =>
    p.title.toLowerCase().includes(filterText.toLowerCase()) ||
    (p.arxiv_id && p.arxiv_id.toLowerCase().includes(filterText.toLowerCase()))
  );

  if (filtered.length === 0) {
    container.innerHTML = `<div class="text-center py-8 text-slate-500 text-xs">No matching papers found.</div>`;
    return;
  }

  container.innerHTML = filtered.map((p) => {
    const isSelected = state.activePaper && state.activePaper.id === p.id;
    return `
      <div class="paper-card group relative p-3 rounded-xl border transition cursor-pointer ${
        isSelected
          ? 'bg-indigo-950/50 border-indigo-600/70'
          : 'bg-slate-900 border-slate-800 hover:border-slate-700'
      }" onclick="selectPaper('${p.id}')">
        <div class="flex items-start justify-between gap-1">
          <h4 class="text-xs font-semibold text-slate-200 line-clamp-2 leading-snug group-hover:text-white">
            ${p.title}
          </h4>
          <button onclick="event.stopPropagation(); deletePaper('${p.id}')" 
                  class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 p-1 transition" title="Delete Paper">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
        <div class="flex items-center justify-between text-[11px] text-slate-400 mt-2">
          <span>${p.arxiv_id ? 'arXiv:' + p.arxiv_id : 'PDF'}</span>
          <span>${p.num_pages} pages</span>
        </div>
      </div>
    `;
  }).join('');

  lucide.createIcons();
}

async function selectPaper(paperId) {
  try {
    const res = await fetch(`/api/papers/${paperId}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    state.activePaper = data.paper;
    state.activeAnalysis = data.analysis;
    state.chatHistory = [];

    renderActivePaperView();
    setMode('analysis');
    renderPaperList();
  } catch (err) {
    alert('Failed to select paper: ' + err.message);
  }
}

async function deletePaper(paperId) {
  if (!confirm('Are you sure you want to remove this paper and its analysis?')) return;
  try {
    await fetch(`/api/papers/${paperId}`, { method: 'DELETE' });
    if (state.activePaper && state.activePaper.id === paperId) {
      state.activePaper = null;
      state.activeAnalysis = null;
      showIngestionView();
    }
    await loadPaperLibrary();
  } catch (err) {
    alert('Delete failed: ' + err.message);
  }
}

function showIngestionView() {
  state.activePaper = null;
  state.activeAnalysis = null;
  elements.viewIngestion.classList.remove('hidden');
  elements.viewAnalysis.classList.add('hidden');
  elements.viewCompare.classList.add('hidden');
  renderPaperList();
}

// Display Active Paper
function renderActivePaperView() {
  if (!state.activePaper) return;

  elements.viewIngestion.classList.add('hidden');
  elements.viewCompare.classList.add('hidden');
  elements.viewAnalysis.classList.remove('hidden');

  const p = state.activePaper;
  elements.bannerTitle.innerText = p.title;
  elements.bannerAuthors.innerText = p.authors && p.authors.length > 0 ? p.authors.join(', ') : 'Unknown Authors';
  elements.bannerPagesBadge.innerText = `${p.num_pages} Pages`;
  elements.bannerWordsBadge.innerText = `${p.word_count.toLocaleString()} Words`;

  if (p.arxiv_id) {
    elements.bannerArxivBadge.innerText = `arXiv: ${p.arxiv_id}`;
    elements.bannerArxivBadge.classList.remove('hidden');
  } else {
    elements.bannerArxivBadge.classList.add('hidden');
  }

  // Update export links
  elements.exportMd.href = `/api/export/${p.id}?format=md`;
  elements.exportHtml.href = `/api/export/${p.id}?format=html`;
  elements.exportJson.href = `/api/export/${p.id}?format=json`;

  // Render current tab content
  switchSectionTab(state.activeTab);
  loadChatStarters(p.id);
}

// Tab Switching
function switchSectionTab(tabKey) {
  state.activeTab = tabKey;

  // Highlight active tab button
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    if (btn.getAttribute('data-tab') === tabKey) {
      btn.className = 'tab-btn px-4 py-2.5 border-b-2 border-indigo-500 text-indigo-400 flex items-center space-x-2 whitespace-nowrap transition';
    } else {
      btn.className = 'tab-btn px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center space-x-2 whitespace-nowrap transition';
    }
  });

  if (tabKey === 'chat') {
    elements.tabSectionContent.classList.add('hidden');
    elements.tabChatContainer.classList.remove('hidden');
    return;
  }

  elements.tabChatContainer.classList.add('hidden');
  elements.tabSectionContent.classList.remove('hidden');

  // Check if we have analysis for this section
  if (state.activeAnalysis && state.activeAnalysis.sections && state.activeAnalysis.sections[tabKey]) {
    elements.sectionPlaceholder.classList.add('hidden');
    elements.sectionRenderedBody.classList.remove('hidden');
    const sec = state.activeAnalysis.sections[tabKey];
    
    // Parse Markdown and render LaTeX math
    elements.sectionRenderedBody.innerHTML = marked.parse(sec.content);
    if (window.renderMathInElement) {
      renderMathInElement(elements.sectionRenderedBody, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
        ],
      });
    }
  } else {
    elements.sectionPlaceholder.classList.remove('hidden');
    elements.sectionRenderedBody.classList.add('hidden');
  }
}

// Running Full Agent Analysis
async function runFullAnalysis() {
  if (!state.activePaper) return;
  if (state.isAnalyzing) return;

  state.isAnalyzing = true;
  elements.btnRunFull.disabled = true;
  elements.progressBarContainer.classList.remove('hidden');
  elements.progressFill.style.width = '0%';
  elements.progressPercent.innerText = '0%';
  elements.progressMessage.innerText = 'Initializing analysis agent...';

  // Initialize fresh analysis container in state if needed
  if (!state.activeAnalysis) {
    state.activeAnalysis = {
      paper_id: state.activePaper.id,
      paper_title: state.activePaper.title,
      model_used: elements.modelSelect.value,
      sections: {},
    };
  }

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: state.activePaper.id,
        model: elements.modelSelect.value,
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Analysis failed');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop(); // keep partial

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const payload = JSON.parse(line.replace('data: ', ''));
          handleAnalysisEvent(payload);
        }
      }
    }
  } catch (err) {
    alert('Analysis Error: ' + err.message);
  } finally {
    state.isAnalyzing = false;
    elements.btnRunFull.disabled = false;
    elements.progressBarContainer.classList.add('hidden');
    // Refresh active paper details
    await selectPaper(state.activePaper.id);
  }
}

function handleAnalysisEvent(evt) {
  if (evt.event === 'section_start') {
    const pct = Math.round(((evt.index - 1) / evt.total) * 100);
    elements.progressFill.style.width = `${pct}%`;
    elements.progressPercent.innerText = `${pct}%`;
    elements.progressMessage.innerText = `Analyzing: ${evt.title}...`;
  } else if (evt.event === 'section_done') {
    state.activeAnalysis.sections[evt.key] = {
      key: evt.key,
      title: evt.title,
      content: evt.content,
      generation_time_s: evt.duration,
    };
    if (state.activeTab === evt.key) {
      switchSectionTab(evt.key);
    }
  } else if (evt.event === 'section_error') {
    console.error(`Section error for ${evt.key}:`, evt.error);
    elements.progressMessage.innerText = `Warning: ${evt.title} failed (${evt.error})`;
    state.activeAnalysis.sections[evt.key] = {
      key: evt.key,
      title: evt.title,
      content: `> [!WARNING]\n> **Generation Error for ${evt.title}**\n> ${evt.error}\n>\n> *Tip: Try re-running the analysis or choosing Gemini 3.5 Flash in the model dropdown above.*`,
      generation_time_s: 0,
    };
    if (state.activeTab === evt.key) {
      switchSectionTab(evt.key);
    }
  } else if (evt.event === 'complete') {
    elements.progressFill.style.width = '100%';
    elements.progressPercent.innerText = '100%';
    if (evt.success_count === 0) {
      elements.progressMessage.innerText = 'Analysis encountered errors. Please check your model or API key.';
      alert('Analysis failed: Unable to generate report sections. Please ensure Gemini 3.5 Flash is selected.');
    } else {
      elements.progressMessage.innerText = `Analysis complete! (${evt.success_count || Object.keys(state.activeAnalysis.sections).length} sections ready)`;
    }
  }
}

// Chat Engine
async function loadChatStarters(paperId) {
  try {
    const res = await fetch(`/api/chat/starters/${paperId}`);
    const data = await res.json();
    if (data.questions && data.questions.length > 0) {
      elements.chatStartersBox.classList.remove('hidden');
      elements.chatStartersList.innerHTML = data.questions.map((q) => `
        <button onclick="askQuestion('${q.replace(/'/g, "\\'")}')" 
                class="text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/50 p-2.5 rounded-xl text-xs text-indigo-200 transition">
          <i data-lucide="help-circle" class="w-3.5 h-3.5 inline mr-1 text-indigo-400"></i> ${q}
        </button>
      `).join('');
      lucide.createIcons();
    }
  } catch (err) {
    console.error('Failed to load chat starters:', err);
  }
}

window.askQuestion = function(q) {
  elements.chatInput.value = q;
  handleChatSubmit(new Event('submit'));
};

async function handleChatSubmit(e) {
  e.preventDefault();
  const query = elements.chatInput.value.trim();
  if (!query || !state.activePaper) return;

  elements.chatInput.value = '';
  appendChatMessage('user', query);

  // Assistant placeholder bubble
  const assistantBubbleId = 'assistant-msg-' + Date.now();
  appendChatMessage('model', '...', assistantBubbleId);
  const bubbleElem = document.getElementById(assistantBubbleId);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: state.activePaper.id,
        message: query,
        model: elements.modelSelect.value,
        history: state.chatHistory.slice(-6),
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let assistantText = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const payload = JSON.parse(line.replace('data: ', ''));
          if (payload.chunk) {
            assistantText += payload.chunk;
            bubbleElem.innerHTML = marked.parse(assistantText);
            if (window.renderMathInElement) {
              renderMathInElement(bubbleElem, {
                delimiters: [
                  { left: '$$', right: '$$', display: true },
                  { left: '$', right: '$', display: false },
                ],
              });
            }
            elements.chatThread.scrollTop = elements.chatThread.scrollHeight;
          }
        }
      }
    }

    state.chatHistory.push({ role: 'user', content: query });
    state.chatHistory.push({ role: 'model', content: assistantText });
  } catch (err) {
    bubbleElem.innerText = 'Error generating response: ' + err.message;
  }
}

function appendChatMessage(role, text, customId = null) {
  const isUser = role === 'user';
  const msgHtml = `
    <div class="flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}">
      <div class="w-7 h-7 rounded-lg ${isUser ? 'bg-slate-700' : 'bg-indigo-600'} flex items-center justify-center flex-shrink-0">
        <i data-lucide="${isUser ? 'user' : 'bot'}" class="w-4 h-4 text-white"></i>
      </div>
      <div id="${customId || ''}" class="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-xs sm:text-sm text-slate-200 max-w-2xl prose prose-invert">
        ${marked.parse(text)}
      </div>
    </div>
  `;
  elements.chatThread.insertAdjacentHTML('beforeend', msgHtml);
  lucide.createIcons();
  elements.chatThread.scrollTop = elements.chatThread.scrollHeight;
}

// Comparative Mode
function setMode(mode) {
  state.currentMode = mode;
  if (mode === 'analysis') {
    elements.modeAnalysisBtn.className = 'py-1 px-2 rounded text-center transition bg-indigo-600 text-white';
    elements.modeCompareBtn.className = 'py-1 px-2 rounded text-center transition text-slate-400 hover:text-white';
    if (state.activePaper) {
      elements.viewAnalysis.classList.remove('hidden');
      elements.viewCompare.classList.add('hidden');
      elements.viewIngestion.classList.add('hidden');
    } else {
      showIngestionView();
    }
  } else {
    elements.modeCompareBtn.className = 'py-1 px-2 rounded text-center transition bg-indigo-600 text-white';
    elements.modeAnalysisBtn.className = 'py-1 px-2 rounded text-center transition text-slate-400 hover:text-white';
    elements.viewAnalysis.classList.add('hidden');
    elements.viewIngestion.classList.add('hidden');
    elements.viewCompare.classList.remove('hidden');
    renderCompareSelection();
  }
}

function renderCompareSelection() {
  const container = elements.compareSelectionList;
  if (state.papers.length === 0) {
    container.innerHTML = `<span class="text-xs text-slate-500">No papers available to compare. Add papers first.</span>`;
    return;
  }

  container.innerHTML = state.papers.map((p) => `
    <label class="flex items-center space-x-2 bg-slate-900 border border-slate-800 hover:border-slate-700 p-2.5 rounded-xl cursor-pointer text-xs">
      <input type="checkbox" value="${p.id}" class="compare-checkbox rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0">
      <span class="text-slate-200 truncate font-medium">${p.title}</span>
    </label>
  `).join('');
}

async function runComparison() {
  const checkboxes = document.querySelectorAll('.compare-checkbox:checked');
  const selectedIds = Array.from(checkboxes).map((c) => c.value);

  if (selectedIds.length < 2) {
    alert('Please select at least 2 papers to compare.');
    return;
  }

  elements.btnRunCompare.disabled = true;
  elements.compareResultPlaceholder.classList.add('hidden');
  elements.compareRenderedBody.classList.remove('hidden');
  elements.compareRenderedBody.innerHTML = '<span class="text-indigo-400 animate-pulse text-sm">Synthesizing comparative analysis across papers...</span>';

  try {
    const response = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_ids: selectedIds,
        model: elements.modelSelect.value,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullReport = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const payload = JSON.parse(line.replace('data: ', ''));
          if (payload.chunk) {
            fullReport += payload.chunk;
            elements.compareRenderedBody.innerHTML = marked.parse(fullReport);
            if (window.renderMathInElement) {
              renderMathInElement(elements.compareRenderedBody, {
                delimiters: [
                  { left: '$$', right: '$$', display: true },
                  { left: '$', right: '$', display: false },
                ],
              });
            }
          }
        }
      }
    }
  } catch (err) {
    elements.compareRenderedBody.innerText = 'Comparison error: ' + err.message;
  } finally {
    elements.btnRunCompare.disabled = false;
  }
}

