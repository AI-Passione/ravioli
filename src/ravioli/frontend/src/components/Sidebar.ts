import { store } from '../store';
import { api } from '../services/api';

export function renderSidebar() {
  const missions = store.getMissions();
  const activeId = store.getActiveMissionId();

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
          <li><button class="nav-item active flex items-center gap-3" data-tab="missions">
            <i data-lucide="layout-dashboard"></i> <span>Missions</span>
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
          <button class="btn-icon" id="btn-new-mission">
            <i data-lucide="plus"></i>
          </button>
        </div>
        <ul class="space-y-1" id="mission-list">
          ${missions.map(m => `
            <li>
              <button class="nav-item flex items-center gap-3 ${m.id === activeId ? 'active' : ''}" data-mission-id="${m.id}">
                <i data-lucide="message-square"></i>
                <span class="truncate">${m.title}</span>
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
  container.querySelectorAll('[data-mission-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-mission-id');
      if (id) store.setActiveMissionId(id);
    });
  });

  container.querySelector('#btn-new-mission')?.addEventListener('click', async () => {
    const title = prompt('Mission Title:');
    if (title) {
      const newMission = await api.createMission({ title });
      store.setMissions([newMission, ...store.getMissions()]);
      store.setActiveMissionId(newMission.id);
    }
  });

  return container;
}
