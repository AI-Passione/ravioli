import { store } from '../store';
import { api } from '../services/api';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();

export function renderNotebook() {
  const activeId = store.getActiveMissionId();
  const missions = store.getMissions();
  const mission = missions.find(m => m.id === activeId);
  const logs = store.getLogs();

  const container = document.createElement('div');
  container.className = 'flex-1 overflow-y-auto relative px-16 pt-10 pb-32';

  if (!mission) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center h-[60vh] text-[#a38b88]">
        <h2 class="mb-4">Select a Mission</h2>
        <p class="label opacity-60">The Silent Concierge is waiting.</p>
      </div>
    `;
    return container;
  }

  container.innerHTML = `
    <header class="mb-16">
      <h2 class="mb-2 text-white">${mission.title}</h2>
      <div class="flex items-center gap-4">
        <span class="label text-[#eac34a]">${mission.status}</span>
        <span class="label text-[#554240]"># ${logs.length} Steps</span>
      </div>
    </header>

    <div class="space-y-4" id="cell-container">
      ${logs.map(log => `
        <div class="group relative mb-8 rounded-md transition-all ${log.log_type === 'user_query' ? 'surface-lowest p-4' : 'glass p-6'}">
          <div class="flex items-center justify-between mb-4">
            <span class="label text-[#a38b88]">${log.log_type === 'user_query' ? 'User Inquiry' : 'Agent Response'}</span>
          </div>
          <div class="prose prose-invert text-[#d1d5db] leading-relaxed">
            ${md.render(log.content)}
          </div>
        </div>
      `).join('')}
      
      <!-- Interaction Cell -->
      <div class="surface-lowest p-4 rounded-md mb-8">
        <div class="flex items-center mb-4">
          <span class="label text-[#a38b88]">New Question</span>
        </div>
        <div class="flex gap-4 items-start">
          <textarea id="cell-input" class="cell-input" placeholder="Ask a question..."></textarea>
          <button id="btn-execute" class="btn-gold">
            <i data-lucide="play"></i>
          </button>
        </div>
      </div>
    </div>
  `;

  const input = container.querySelector('#cell-input') as HTMLTextAreaElement;
  const btn = container.querySelector('#btn-execute');

  btn?.addEventListener('click', async () => {
    const question = input.value;
    if (!question || !activeId) return;
    
    input.value = '';
    btn.setAttribute('disabled', 'true');
    btn.classList.add('opacity-50');

    try {
      await api.askQuestion(activeId, question);
      // Polling will pick up the new logs
    } catch (err) {
      alert('Failed to submit question');
    } finally {
      btn.removeAttribute('disabled');
      btn.classList.remove('opacity-50');
    }
  });

  return container;
}
