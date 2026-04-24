import { store } from '../store';

export function renderSidebar() {
  const analyses = store.getAnalyses();
  const activeId = store.getActiveAnalysisId();

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
      <a href="https://github.com/AI-Passione/ravioli" target="_blank" rel="noopener noreferrer" class="text-neutral-500 hover:text-white transition-colors p-1" title="GitHub Repository">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.042-1.416-4.042-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.744.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
        </svg>
      </a>
    </div>

    <!-- Navigation Links -->
    <nav class="flex-1 space-y-2">
      <section class="mb-8">
        <p class="text-[10px] uppercase tracking-[0.2em] text-outline px-8 mb-4 opacity-50">Vibe Analytics</p>
        <div class="space-y-1">
          <button class="nav-item ${store.getCurrentView() === 'dashboard' && !activeId ? 'active' : ''} w-full" data-nav="home">
            <span class="material-symbols-outlined text-primary-fixed-dim" data-icon="dashboard">dashboard</span>
            <span>Analyses</span>
          </button>
          <button class="nav-item w-full" data-nav="warehouse">
            <span class="material-symbols-outlined" data-icon="storage">storage</span>
            <span>Warehouse</span>
          </button>
        </div>
      </section>

      <section>
        <div class="flex items-center justify-between px-8 mb-4">
          <p class="text-[10px] uppercase tracking-[0.2em] text-outline opacity-50 text-label-sm">Investigations</p>
          <button class="text-primary-fixed-dim hover:text-white transition-colors" id="btn-new-analysis">
            <span class="material-symbols-outlined text-sm" data-icon="add">add</span>
          </button>
        </div>
        <ul class="space-y-1 overflow-y-auto max-h-[40vh]" id="analysis-list">
          ${analyses.map(a => `
            <li>
              <button class="nav-item w-full ${a.id === activeId ? 'active' : ''}" data-analysis-id="${a.id}">
                <span class="material-symbols-outlined ${a.id === activeId ? 'text-primary-fixed-dim' : ''}" data-icon="analytics">analytics</span>
                <span class="truncate">${a.title}</span>
              </button>
            </li>
          `).join('')}
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

  container.querySelectorAll('[data-analysis-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-analysis-id');
      if (id) store.setActiveAnalysisId(id);
    });
  });

  container.querySelector('#btn-new-analysis')?.addEventListener('click', () => {
    store.setCurrentView('create-analysis');
  });

  container.querySelector('[data-nav="home"]')?.addEventListener('click', () => {
    store.setCurrentView('dashboard');
    store.setActiveAnalysisId(undefined);
  });

  return container;
}
