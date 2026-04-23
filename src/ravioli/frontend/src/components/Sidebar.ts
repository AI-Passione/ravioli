import { store } from '../store';
import { api } from '../services/api';

export function renderSidebar() {
  const analyses = store.getAnalyses();
  const activeId = store.getActiveAnalysisId();

  const container = document.createElement('aside');
  container.className = 'w-64 h-screen surface-low flex flex-col pt-8 pb-4 px-4 overflow-y-auto';

  container.innerHTML = `
    <div class="flex items-center gap-3 mb-10 px-2">
      <div class="w-8 h-8 rounded-sm bg-gradient-to-br from-[#ffb3b5] to-[#4c000f]"></div>
      <h1 class="text-xl font-display tracking-tight text-white">Ravioli</h1>
    </div>

    <nav class="space-y-8 flex-1">
      <section>
        <p class="label text-[#a38b88] mb-4 px-2">System</p>
        <ul class="space-y-1">
          <li><button class="nav-item active flex items-center gap-3" data-tab="analyses">
            <i data-lucide="layout-dashboard"></i> <span>Analyses</span>
          </button></li>
          <li><button class="nav-item flex items-center gap-3" data-tab="warehouse">
            <i data-lucide="database"></i> <span>Warehouse</span>
          </button></li>
          <li><button class="nav-item flex items-center gap-3" data-tab="settings">
            <i data-lucide="settings"></i> <span>Settings</span>
          </button></li>
        </ul>
      </section>

      <section>
        <div class="flex items-center justify-between mb-4 px-2">
          <p class="label text-[#a38b88]">Investigations</p>
          <button class="btn-icon" id="btn-new-analysis">
            <i data-lucide="plus"></i>
          </button>
        </div>
        <ul class="space-y-1" id="analysis-list">
          ${analyses.map(a => `
            <li>
              <button class="nav-item flex items-center gap-3 ${a.id === activeId ? 'active' : ''}" data-analysis-id="${a.id}">
                <i data-lucide="message-square"></i>
                <span class="truncate">${a.title}</span>
              </button>
            </li>
          `).join('')}
        </ul>
      </section>
    </nav>

    <div class="px-2 pt-4 border-t border-[#554240] opacity-20">
      <p class="label text-[10px]">AI Passione &copy; 2026</p>
    </div>
  `;

  // Event Listeners
  container.querySelectorAll('[data-analysis-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-analysis-id');
      if (id) store.setActiveAnalysisId(id);
    });
  });

  container.querySelector('#btn-new-analysis')?.addEventListener('click', async () => {
    const title = prompt('Analysis Title:');
    if (title) {
      const newAnalysis = await api.createAnalysis({ title });
      store.setAnalyses([newAnalysis, ...store.getAnalyses()]);
      store.setActiveAnalysisId(newAnalysis.id);
    }
  });

  return container;
}
