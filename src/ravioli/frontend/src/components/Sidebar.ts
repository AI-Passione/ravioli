import { store } from '../store';

export function renderSidebar() {
  const analyses = store.getAnalyses();
  const activeId = store.getActiveAnalysisId();
  const currentView = store.getCurrentView();

  const container = document.createElement('aside');
  container.className = 'fixed left-0 top-0 flex flex-col h-full py-8 w-64 bg-surface-container-low font-display-lg text-sm tracking-tight z-50';

  container.innerHTML = `
    <!-- Brand Header -->
    <div class="px-8 mb-12 flex items-center justify-between">
      <div class="flex items-center gap-3 cursor-pointer" id="brand-header">
        <img src="/ravioli-logo.png" alt="Ravioli Logo" class="w-8 h-8 rounded-lg shadow-lg shadow-primary/20">
        <div class="flex flex-col">
          <div class="text-xl font-medium tracking-tight text-neutral-100">Ravioli</div>
          <div class="text-[9px] uppercase tracking-[0.2em] text-primary-fixed-dim opacity-70 -mt-0.5">AI Analytics Platform</div>
        </div>
      </div>
    </div>

    <!-- Navigation Links -->
    <nav class="flex-1 space-y-2">
      <section class="mb-8">
        <p class="text-[10px] uppercase tracking-[0.2em] text-outline px-8 mb-4 opacity-50">Vibe Analytics</p>
        <div class="space-y-1">
          <button class="nav-item ${currentView === 'dashboard' && !activeId ? 'active' : ''} w-full" data-nav="dashboard">
            <span class="material-symbols-outlined text-primary-fixed-dim" data-icon="dashboard">dashboard</span>
            <span>Dashboard</span>
          </button>
          <button class="nav-item ${currentView === 'knowledge' ? 'active' : ''} w-full" data-nav="knowledge">
            <span class="material-symbols-outlined" data-icon="local_library">local_library</span>
            <span>Knowledge</span>
          </button>
          <button class="nav-item ${currentView === 'data' ? 'active' : ''} w-full" data-nav="data">
            <span class="material-symbols-outlined" data-icon="storage">storage</span>
            <span>Data</span>
          </button>
        </div>
      </section>

      <section>
        <div class="flex items-center justify-between px-8 mb-4">
          <p class="text-[10px] uppercase tracking-[0.2em] text-outline opacity-50 text-label-sm">Analyses</p>
          <button class="text-primary-fixed-dim hover:text-white transition-colors" id="btn-new-analysis">
            <span class="material-symbols-outlined text-sm" data-icon="add">add</span>
          </button>
        </div>
        <ul class="space-y-1 overflow-y-auto max-h-[40vh]" id="analysis-list">
          ${analyses.map(a => {
            const isQuick = a.analysis_metadata?.type === 'quick_insight';
            const icon = isQuick ? 'bolt' : 'terminal';
            return `
            <li>
              <button class="nav-item w-full ${a.id === activeId ? 'active' : ''}" data-analysis-id="${a.id}">
                <span class="material-symbols-outlined ${a.id === activeId ? 'text-primary-fixed-dim' : ''}" data-icon="${icon}">${icon}</span>
                <span class="truncate">${a.title}</span>
              </button>
            </li>
          `}).join('')}
        </ul>
      </section>
    </nav>

    <!-- User Context -->
    <div class="px-8 mt-auto flex items-center gap-3">
      <div class="w-8 h-8 rounded-full overflow-hidden bg-surface-container-highest">
        <img alt="User profile" class="w-full h-full object-cover grayscale opacity-80" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBm9rkjsFpTTuHvUhgdWXqOVy5TEU6WU0Zmn9L54MAL7rqO9xlW28xICQZTib_IPC3Vni4JRBxl4-Gppy19CJdOHiEcBlPQbvt0gCCA-6kf_AKQm6zQKwMOCZ3IKPJEhInarqydnCUGYEs1zu15jSFIpuA23IZYc2x9_iPo_nEmpEwwPJrLucmJKE2TBrQmAWUvQcXay_vsZJuJE1ijeaMEisbmWS_uXDIJ1QCYQnlPXn6CEQazi2-HIVXCt8NqmI9sueKY83dOles"/>
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] font-label-sm text-on-surface-variant uppercase tracking-widest">OPERATOR</span>
        <span class="text-[12px] font-medium text-neutral-100">Studio Noir</span>
      </div>
    </div>
  `;

  // Event Listeners
  container.querySelector('#brand-header')?.addEventListener('click', () => {
    store.setCurrentView('dashboard');
    store.setActiveAnalysisId(undefined);
  });

  container.querySelector('#btn-new-analysis')?.addEventListener('click', () => {
    store.setCurrentView('create-analysis');
  });

  container.querySelectorAll('[data-nav]').forEach(btn => {
    btn.addEventListener('click', () => {
      const nav = btn.getAttribute('data-nav') as any;
      if (nav) {
        store.setCurrentView(nav);
        store.setActiveAnalysisId(undefined);
      }
    });
  });

  container.querySelectorAll('[data-analysis-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-analysis-id');
      if (id) {
        store.setActiveAnalysisId(id);
      }
    });
  });

  return container;
}
