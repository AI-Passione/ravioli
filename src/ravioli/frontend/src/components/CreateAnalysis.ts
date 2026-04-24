import { store } from '../store';
import { api } from '../services/api';

export function renderCreateAnalysis() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 relative overflow-hidden bg-background h-screen flex flex-col items-center justify-center';

  container.innerHTML = `
    <!-- Cinematic Vignette Overlay -->
    <div class="absolute inset-0 cinematic-vignette"></div>

    <div class="max-w-2xl w-full space-y-12 relative z-10 px-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <div class="text-center space-y-4">
        <h2 class="text-5xl font-display-lg text-on-surface tracking-tight">
          New Sequence
        </h2>
        <p class="font-label-sm text-label-sm tracking-[0.4em] text-tertiary-fixed-dim uppercase">
          The studio is ready for your parameters.
        </p>
      </div>

      <div class="glass-panel p-10 rounded-3xl space-y-8">
        <div class="space-y-8">
          <div class="space-y-2 group">
            <label for="analysis-title" class="text-[10px] font-label-sm text-outline uppercase tracking-widest opacity-60 group-focus-within:opacity-100 transition-opacity">Sequence Title</label>
            <input 
              type="text" 
              id="analysis-title" 
              placeholder="e.g., Market Volatility Analysis" 
              class="w-full bg-transparent border-b border-outline-variant/30 py-3 text-white focus:outline-none focus:border-primary-fixed-dim transition-colors text-xl font-headline-sm"
            />
          </div>

          <div class="space-y-2 group">
            <label for="analysis-desc" class="text-[10px] font-label-sm text-outline uppercase tracking-widest opacity-60 group-focus-within:opacity-100 transition-opacity">Operational Context</label>
            <textarea 
              id="analysis-desc" 
              placeholder="What mysteries shall we unravel today?" 
              rows="3"
              class="w-full bg-transparent border-b border-outline-variant/30 py-3 text-on-surface-variant focus:outline-none focus:border-primary-fixed-dim transition-colors resize-none font-body-lg"
            ></textarea>
          </div>
        </div>

        <div class="flex items-center justify-end gap-8 pt-4">
          <button id="cancel-create" class="text-sm font-label-sm text-outline hover:text-white uppercase tracking-widest transition-colors">
            Abort
          </button>
          <button id="confirm-create" class="btn-primary flex items-center gap-3 group">
            <span>Initialize</span>
            <span class="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform" data-icon="rocket_launch">rocket_launch</span>
          </button>
        </div>
      </div>
      
      <div class="grid grid-cols-3 gap-8 opacity-20">
         <div class="text-center space-y-2">
            <span class="material-symbols-outlined text-tertiary" data-icon="database">database</span>
            <p class="text-[10px] font-label-sm uppercase tracking-widest">Neural Link</p>
         </div>
         <div class="text-center space-y-2">
            <span class="material-symbols-outlined text-primary" data-icon="auto_awesome">auto_awesome</span>
            <p class="text-[10px] font-label-sm uppercase tracking-widest">Core Logic</p>
         </div>
         <div class="text-center space-y-2">
            <span class="material-symbols-outlined text-secondary" data-icon="monitoring">monitoring</span>
            <p class="text-[10px] font-label-sm uppercase tracking-widest">Data Stream</p>
         </div>
      </div>
    </div>

    <!-- Soft Glow -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none"></div>
  `;

  // Event Listeners
  container.querySelector('#cancel-create')?.addEventListener('click', () => {
    store.setCurrentView('dashboard');
  });

  container.querySelector('#confirm-create')?.addEventListener('click', async () => {
    const titleInput = container.querySelector('#analysis-title') as HTMLInputElement;
    const descInput = container.querySelector('#analysis-desc') as HTMLTextAreaElement;
    
    const title = titleInput.value.trim();
    if (!title) {
      titleInput.classList.add('border-error');
      return;
    }

    const btn = container.querySelector('#confirm-create') as HTMLButtonElement;
    btn.disabled = true;
    btn.innerHTML = '<span>Initializing Sequence...</span>';

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
      btn.innerHTML = '<span>Initialize</span>';
    }
  });

  return container;
}
