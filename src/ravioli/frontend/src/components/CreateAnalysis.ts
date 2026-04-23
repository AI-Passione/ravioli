import { store } from '../store';
import { api } from '../services/api';

export function renderCreateAnalysis() {
  const container = document.createElement('main');
  container.className = 'flex-1 h-screen overflow-y-auto bg-[#1a1414] text-white p-12 flex flex-col items-center justify-center';

  container.innerHTML = `
    <div class="max-w-2xl w-full space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <div class="text-center space-y-4">
        <h2 class="text-4xl font-display font-medium tracking-tight bg-gradient-to-r from-white to-[#a38b88] bg-clip-text text-transparent">
          Start a New Investigation
        </h2>
        <p class="text-[#a38b88] text-lg">
          Define your analysis goal and let the agents do the heavy lifting.
        </p>
      </div>

      <div class="glass-panel p-8 rounded-2xl border border-white/5 space-y-8">
        <div class="space-y-6">
          <div class="space-y-2">
            <label for="analysis-title" class="text-sm font-medium text-[#a38b88] uppercase tracking-wider">Analysis Title</label>
            <input 
              type="text" 
              id="analysis-title" 
              placeholder="e.g., Substack Growth Analysis Q1" 
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#ffb3b5]/50 transition-colors text-lg"
            />
          </div>

          <div class="space-y-2">
            <label for="analysis-desc" class="text-sm font-medium text-[#a38b88] uppercase tracking-wider">Description (Optional)</label>
            <textarea 
              id="analysis-desc" 
              placeholder="What are you looking to discover?" 
              rows="4"
              class="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#ffb3b5]/50 transition-colors resize-none"
            ></textarea>
          </div>
        </div>

        <div class="flex items-center justify-end gap-4 pt-4">
          <button id="cancel-create" class="px-6 py-3 text-[#a38b88] hover:text-white transition-colors">
            Cancel
          </button>
          <button id="confirm-create" class="btn-primary flex items-center gap-2 group">
            <span>Initialize Analysis</span>
            <i data-lucide="play" class="w-4 h-4 group-hover:translate-x-1 transition-transform"></i>
          </button>
        </div>
      </div>
      
      <div class="grid grid-cols-3 gap-4 opacity-50">
         <div class="glass-panel p-4 rounded-xl border border-white/5 text-center space-y-2">
            <div class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mx-auto">
               <i data-lucide="database" class="w-5 h-5 text-[#ffb3b5]"></i>
            </div>
            <p class="text-xs font-medium">Auto-Ingest</p>
         </div>
         <div class="glass-panel p-4 rounded-xl border border-white/5 text-center space-y-2">
            <div class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mx-auto">
               <i data-lucide="message-square" class="w-5 h-5 text-[#ffb3b5]"></i>
            </div>
            <p class="text-xs font-medium">AI Insights</p>
         </div>
         <div class="glass-panel p-4 rounded-xl border border-white/5 text-center space-y-2">
            <div class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mx-auto">
               <i data-lucide="layout-dashboard" class="w-5 h-5 text-[#ffb3b5]"></i>
            </div>
            <p class="text-xs font-medium">Live Reports</p>
         </div>
      </div>
    </div>
  `;

  // Event Listeners
  container.querySelector('#cancel-create')?.addEventListener('click', () => {
    store.setCurrentView('dashboard');
    const analyses = store.getAnalyses();
    if (analyses.length > 0) {
      store.setActiveAnalysisId(analyses[0].id);
    }
  });

  container.querySelector('#confirm-create')?.addEventListener('click', async () => {
    const titleInput = container.querySelector('#analysis-title') as HTMLInputElement;
    const descInput = container.querySelector('#analysis-desc') as HTMLTextAreaElement;
    
    const title = titleInput.value.trim();
    if (!title) {
      titleInput.classList.add('border-red-500/50');
      return;
    }

    const btn = container.querySelector('#confirm-create') as HTMLButtonElement;
    btn.disabled = true;
    btn.innerHTML = '<span>Initializing...</span>';

    try {
      const newAnalysis = await api.createAnalysis({ 
        title, 
        description: descInput.value.trim() 
      });
      store.setAnalyses([newAnalysis, ...store.getAnalyses()]);
      store.setActiveAnalysisId(newAnalysis.id);
    } catch (err) {
      console.error('Failed to create analysis', err);
      btn.disabled = false;
      btn.innerHTML = '<span>Initialize Analysis</span>';
    }
  });

  return container;
}
