import { store } from '../store';
import { api } from '../services/api';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();

export function renderNotebook() {
  const activeId = store.getActiveAnalysisId();
  const analyses = store.getAnalyses();
  const analysis = analyses.find(a => a.id === activeId);
  const logs = store.getLogs();

  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 relative overflow-hidden bg-background h-screen flex flex-col';

  if (!analysis) {
    container.innerHTML = `
      <!-- TopAppBar -->
      <header class="flex justify-end items-center px-12 w-full h-16 absolute top-0 right-0 z-40 bg-transparent">
        <div class="flex items-center gap-8">
          <button class="material-symbols-outlined text-neutral-400 hover:text-neutral-100 transition-all" data-icon="notifications">notifications</button>
          <button class="material-symbols-outlined text-neutral-400 hover:text-neutral-100 transition-all" data-icon="account_circle">account_circle</button>
        </div>
      </header>

      <!-- Cinematic Vignette Overlay -->
      <div class="absolute inset-0 cinematic-vignette"></div>

      <!-- Empty State -->
      <div class="h-full w-full flex flex-col items-center justify-center relative z-10 px-margin">
        <div class="w-px h-24 bg-gradient-to-b from-transparent via-tertiary/30 to-transparent mb-scale-16"></div>
        <h1 class="font-display-lg text-display-lg text-on-surface mb-4 tracking-tight">Select an Analysis</h1>
        <p class="font-label-sm text-label-sm tracking-[0.4em] text-tertiary-fixed-dim uppercase">The silent concierge is waiting.</p>
        
        <div class="mt-scale-16 flex items-center gap-4">
          <div class="flex items-center gap-2 px-4 py-2 bg-surface-container-lowest/50 backdrop-blur-md rounded-full border border-outline-variant/10">
            <span class="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse"></span>
            <span class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest">System Ready</span>
          </div>
        </div>

        <div class="absolute bottom-16 right-16 opacity-10">
          <div class="font-display-lg text-[120px] font-thin text-on-surface-variant select-none pointer-events-none italic">V</div>
        </div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none"></div>
      </div>

      <!-- Action Floating Group -->
      <div class="absolute bottom-12 left-1/2 -translate-x-1/2 z-20 flex gap-12">
        <button class="group flex flex-col items-center gap-2" id="btn-new-sequence">
          <div class="p-4 rounded-full border border-outline-variant/20 group-hover:border-tertiary/50 transition-all duration-500 bg-surface-container-low">
            <span class="material-symbols-outlined text-on-surface-variant group-hover:text-tertiary" data-icon="add">add</span>
          </div>
          <span class="font-label-sm text-label-sm text-neutral-500 group-hover:text-neutral-300 tracking-tighter transition-colors uppercase">New Sequence</span>
        </button>
        <button class="group flex flex-col items-center gap-2">
          <div class="p-4 rounded-full border border-outline-variant/20 group-hover:border-primary/50 transition-all duration-500 bg-surface-container-low">
            <span class="material-symbols-outlined text-on-surface-variant group-hover:text-primary" data-icon="auto_awesome">auto_awesome</span>
          </div>
          <span class="font-label-sm text-label-sm text-neutral-500 group-hover:text-neutral-300 tracking-tighter transition-colors uppercase">AI Discovery</span>
        </button>
      </div>
    `;
    
    container.querySelector('#btn-new-sequence')?.addEventListener('click', () => {
      store.setCurrentView('create-analysis');
    });

    return container;
  }

  // Active Analysis Rendering
  container.innerHTML = `
    <header class="flex justify-between items-center px-12 py-8 bg-surface-container-low border-b border-outline-variant/10 z-10">
      <div class="space-y-1">
        <h2 class="text-2xl font-headline-lg text-white">${analysis.title}</h2>
        <div class="flex items-center gap-4">
          <span class="flex items-center gap-2 text-xs font-label-md text-tertiary uppercase tracking-widest">
            <span class="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse"></span>
            ${analysis.status}
          </span>
          <span class="text-[10px] text-outline uppercase tracking-widest font-label-sm opacity-50"># ${logs.length} Steps</span>
        </div>
      </div>
      <div class="flex items-center gap-4">
        <button class="p-2 text-outline hover:text-white transition-colors">
          <span class="material-symbols-outlined" data-icon="settings">settings</span>
        </button>
        <button class="p-2 text-outline hover:text-white transition-colors">
          <span class="material-symbols-outlined" data-icon="share">share</span>
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto px-12 py-8 space-y-12" id="cell-container">
      ${analysis.result ? `
        <div class="glass-panel p-10 rounded-3xl space-y-6 border-primary/20 bg-primary/5 animate-in fade-in slide-in-from-bottom-8 duration-1000">
          <div class="flex items-center gap-4 text-primary">
            <span class="material-symbols-outlined text-3xl" data-icon="auto_awesome">auto_awesome</span>
            <h3 class="text-xl font-headline-sm uppercase tracking-widest">Executive Insights</h3>
          </div>
          <div class="prose prose-invert max-w-none text-on-surface-variant leading-relaxed font-body-lg">
            ${md.render(analysis.result)}
          </div>
          <div class="flex items-center gap-2 pt-4 opacity-40">
            <span class="material-symbols-outlined text-sm" data-icon="verified">verified</span>
            <span class="text-[10px] uppercase tracking-widest font-label-sm">Validated by Local LLM Node</span>
          </div>
        </div>
      ` : ''}

      ${logs.map(log => `
        <div class="group animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="flex items-center gap-4 mb-4">
             <div class="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center">
                <span class="material-symbols-outlined text-sm ${log.log_type === 'user_query' ? 'text-primary' : 'text-tertiary'}" data-icon="${log.log_type === 'user_query' ? 'person' : 'smart_toy'}">
                   ${log.log_type === 'user_query' ? 'person' : 'smart_toy'}
                </span>
             </div>
             <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm">
                ${log.log_type === 'user_query' ? 'Operator' : 'Agent Core'}
             </span>
          </div>
          <div class="pl-12">
            <div class="prose prose-invert max-w-none text-on-surface-variant leading-relaxed font-body-lg">
              ${md.render(log.content)}
            </div>
          </div>
        </div>
      `).join('')}

      <!-- Interaction Cell -->
      <div class="pt-12 mt-12 border-t border-outline-variant/10">
        <div class="glass-panel p-6 rounded-2xl group focus-within:border-primary/30 transition-all duration-500">
          <div class="flex gap-6 items-start">
            <div class="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center shrink-0">
               <span class="material-symbols-outlined text-primary" data-icon="edit_note">edit_note</span>
            </div>
            <div class="flex-1 space-y-4">
              <textarea id="cell-input" class="w-full bg-transparent border-none text-on-surface focus:ring-0 resize-none py-2 text-lg font-body-lg" placeholder="What sequence should we initialize next?" rows="1"></textarea>
              <div class="flex justify-end">
                <button id="btn-execute" class="btn-primary flex items-center gap-2 group/btn">
                  <span>Execute</span>
                  <span class="material-symbols-outlined text-sm group-hover/btn:translate-x-1 transition-transform" data-icon="send">send</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  const input = container.querySelector('#cell-input') as HTMLTextAreaElement;
  const btn = container.querySelector('#btn-execute');

  // Auto-resize textarea
  input?.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
  });

  btn?.addEventListener('click', async () => {
    const question = input.value;
    if (!question || !activeId) return;
    
    input.value = '';
    input.style.height = 'auto';
    btn.setAttribute('disabled', 'true');
    btn.classList.add('opacity-50');

    try {
      await api.askQuestion(activeId, question);
    } catch (err) {
      console.error('Failed to submit question', err);
    } finally {
      btn.removeAttribute('disabled');
      btn.classList.remove('opacity-50');
    }
  });

  return container;
}
