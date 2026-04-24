import { store } from '../store';

export function renderSidebar() {
  const analyses = store.getAnalyses() || [];
  const activeId = store.getActiveAnalysisId();
  const currentView = store.getCurrentView();

  const container = document.createElement('aside');
  container.className = 'fixed left-0 top-0 flex flex-col h-full py-8 w-64 bg-surface-container-low font-display-lg text-sm tracking-tight z-50';

  let analysesListHtml = '';
  if (analyses.length === 0) {
    analysesListHtml = '<li class="px-8 py-4 text-neutral-600 italic text-[10px] uppercase tracking-widest">No Analyses found</li>';
  } else {
    analysesListHtml = analyses.map(a => {
      const isQuick = (a as any).analysis_metadata?.type === 'quick_insight';
      const icon = isQuick ? 'bolt' : 'terminal';
      const isActive = a.id === activeId;
      return `
        <li>
          <button class="nav-item w-full ${isActive ? 'active' : ''}" data-analysis-id="${a.id}">
            <span class="material-symbols-outlined ${isActive ? 'text-primary-fixed-dim' : ''}" data-icon="${icon}">${icon}</span>
            <span class="truncate">${a.title}</span>
          </button>
        </li>
      `;
    }).join('');
  }

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
    <nav class="flex-1 space-y-2 overflow-y-auto">
      <section class="mb-8">
        <p class="text-[10px] uppercase tracking-[0.2em] text-outline px-8 mb-4 opacity-50 font-medium">Vibe Analytics</p>
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

      <section class="mt-4">
        <div class="flex items-center justify-between px-8 mb-4">
          <p class="text-[10px] uppercase tracking-[0.2em] text-outline opacity-50 font-medium">Historical Analyses</p>
          <button class="text-primary-fixed-dim hover:text-white transition-colors" id="btn-new-analysis">
            <span class="material-symbols-outlined text-sm" data-icon="add">add</span>
          </button>
        </div>
        <ul class="space-y-1 max-h-[40vh] overflow-y-auto px-4" id="analysis-list">
          ${analysesListHtml}
        </ul>
      </section>
    </nav>

    <!-- User Context -->
    <div class="px-8 mt-auto flex items-center gap-3">
      <div class="w-8 h-8 rounded-full overflow-hidden bg-surface-container-highest">
        <img alt="User profile" class="w-full h-full object-cover grayscale opacity-80" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBm9rkjsFpTTuHvUhgdWXqOVy5TEU6WU0Zmn9L54MAL7rqO9xlW28xICQZTib_IPC3Vni4JRBxl4-Gppy19CJdOHiEcBlPQbvt0gCCA-6kf_AKQm6zQKwMOCZ3IKPJEhInarqydnCUGYEs1zu15jSFIpuA23IZYc2x9_iPo_nEmpEwwPJrLucmJKE2TBrQmAWUvQcXay_vsZJuJE1ijeaMEisbmWS_uXDIJ1QCYQnlPXn6CEQazi2-HIVXCt8NqmI9sueKY83dOles"/>
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] font-label-sm text-on-surface-variant uppercase tracking-widest font-bold">OPERATOR</span>
        <span class="text-[12px] font-medium text-neutral-100">Studio Noir</span>
      </div>
    </div>
  `;

  // Brand header listener
  container.querySelector('#brand-header')?.addEventListener('click', () => {
    store.setCurrentView('dashboard');
    store.setActiveAnalysisId(undefined);
  });

  // Navigation listeners
  container.querySelectorAll('[data-nav]').forEach(btn => {
    btn.addEventListener('click', () => {
      const nav = btn.getAttribute('data-nav') as any;
      if (nav) {
        store.setCurrentView(nav);
        store.setActiveAnalysisId(undefined);
      }
    });
  });

  // Analysis item listeners
  container.querySelectorAll('[data-analysis-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-analysis-id');
      if (id) {
        store.setActiveAnalysisId(id);
      }
    });
  });

  // New analysis listener
  container.querySelector('#btn-new-analysis')?.addEventListener('click', () => {
    store.setCurrentView('create-analysis');
  });

  return container;
}
