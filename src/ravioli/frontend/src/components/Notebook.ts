import { store } from '../store';
import { api } from '../services/api';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

function renderMarkdown(content: string) {
  if (!content) return '';
  
  // Transform GitHub style alerts: > [!TYPE]
  // This regex matches the blockquote with alert marker
  let transformed = content.replace(/^> \[!(IMPORTANT|NOTE|TIP|WARNING|CAUTION)\]\n((?:>.*\n?)+)/gm, (match, type, body) => {
    const lowerType = type.toLowerCase();
    const icon = type === 'IMPORTANT' ? 'priority_high' : 'info';
    // Remove the leading '>' from each line of the body
    const cleanBody = body.split('\n').map(line => line.replace(/^>\s?/, '')).join('\n');
    return `
<div class="markdown-alert markdown-alert-${lowerType}">
  <div class="markdown-alert-title">
    <span class="material-symbols-outlined text-sm" data-icon="${icon}">${icon}</span>
    <span>${type}</span>
  </div>
  <div class="markdown-alert-content">
    ${md.render(cleanBody.trim())}
  </div>
</div>
`;
  });

  return md.render(transformed);
}

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

    <div class="flex-1 overflow-y-auto px-12 pt-8 pb-32 space-y-12 custom-scrollbar" id="cell-container">
      ${analysis.result ? `
        <div class="glass-panel p-12 rounded-[2rem] space-y-8 border-primary/20 bg-primary/[0.02] animate-in fade-in slide-in-from-bottom-8 duration-1000 relative overflow-hidden group">
          <!-- Subtle glow background -->
          <div class="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 rounded-full blur-[80px] group-hover:bg-primary/20 transition-colors duration-1000"></div>
          
          <div class="flex items-center gap-4 text-primary relative z-10">
            <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-2xl" data-icon="auto_awesome">auto_awesome</span>
            </div>
            <h3 class="text-xl font-headline-sm uppercase tracking-[0.2em]">Executive Insights</h3>
          </div>
          
          <div class="prose prose-invert max-w-none text-on-surface-variant leading-relaxed font-body-lg relative z-10">
            ${renderMarkdown(analysis.result)}
          </div>
          
          ${analysis.analysis_metadata?.followup_questions?.length ? `
            <div class="pt-12 border-t border-outline-variant/10 space-y-6 relative z-10">
              <div class="flex items-center gap-3 text-tertiary">
                <span class="material-symbols-outlined text-xl" data-icon="explore">explore</span>
                <p class="text-[10px] font-label-md uppercase tracking-[0.3em]">Follow-up Sequences</p>
              </div>
              <div class="grid grid-cols-1 gap-3">
                ${analysis.analysis_metadata.followup_questions.map((q: string) => `
                  <button class="followup-question-btn flex items-center justify-between w-full px-6 py-4 text-left text-sm font-body-md text-on-surface-variant bg-surface-container-low hover:bg-surface-container-high border border-outline-variant/10 rounded-xl transition-all duration-300 group hover:border-primary/30 hover:translate-x-1" data-question="${q.replace(/"/g, '&quot;')}">
                    <span class="group-hover:text-white transition-colors">${q}</span>
                    <span class="material-symbols-outlined text-outline group-hover:text-primary transition-colors text-lg opacity-0 group-hover:opacity-100" data-icon="arrow_forward_ios">arrow_forward_ios</span>
                  </button>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <div class="flex items-center justify-between pt-6 border-t border-outline-variant/10 relative z-10">
            <div class="flex items-center gap-2 opacity-40 hover:opacity-100 transition-opacity">
              <span class="material-symbols-outlined text-sm" data-icon="verified">verified</span>
              <span class="text-[10px] uppercase tracking-widest font-label-sm">Validated by Local LLM Node</span>
            </div>
            <div class="flex gap-4">
               <span class="text-[10px] text-outline uppercase tracking-widest opacity-40">System: Studio Noir</span>
            </div>
          </div>
        </div>
      ` : ''}

      ${logs.map(log => `
        <div class="group animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="flex items-center gap-4 mb-4">
             <div class="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center shrink-0 overflow-hidden border border-outline-variant/20">
                ${log.log_type === 'user_query' 
                  ? `<span class="material-symbols-outlined text-outline text-sm" data-icon="person">person</span>` 
                  : `<img src="/src/assets/kowalski.png" class="w-full h-full object-cover" alt="Kowalski">`}
             </div>
             <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm">
                ${log.log_type === 'user_query' ? 'Operator' : 'Kowalski'}
             </span>
          </div>
          <div class="pl-12">
            <div class="prose prose-invert max-w-none text-on-surface-variant leading-relaxed font-body-lg">
              ${renderMarkdown(log.content)}
            </div>
          </div>
        </div>
      `).join('')}
    </div>

    <!-- Floating Interaction Cell (Perplexity Style) -->
    <div class="w-full px-12 pb-12 pt-6 bg-gradient-to-t from-background via-background/90 to-transparent relative z-20">
      <div class="max-w-4xl mx-auto relative">
        <div class="glass-panel p-2 rounded-[2rem] group focus-within:border-primary/30 transition-all duration-500 shadow-2xl shadow-primary/5">
          <div class="flex items-center gap-4 px-4">
            <div class="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center shrink-0">
               <span class="material-symbols-outlined text-primary text-xl" data-icon="auto_awesome">auto_awesome</span>
            </div>
            <div class="flex-1 min-w-0 py-2">
              <textarea id="cell-input" class="w-full bg-transparent border-none text-on-surface focus:ring-0 resize-none py-2 text-lg font-body-lg max-h-48 custom-scrollbar" placeholder="Ask Kowalski a follow-up question..." rows="1"></textarea>
            </div>
            <div class="flex items-center pr-2">
              <button id="btn-execute" class="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center hover:scale-110 transition-transform disabled:opacity-50 disabled:scale-100 group/btn shadow-lg shadow-primary/20">
                <span class="material-symbols-outlined text-xl group-hover/btn:translate-x-0.5 transition-transform" data-icon="arrow_forward">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Subtle Status Hint -->
        <div class="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none">
          <span class="text-[10px] uppercase tracking-[0.3em] text-primary/50 font-label-sm">Kowalski Neural Link Active</span>
        </div>
      </div>
    </div>
  `;

  // Auto-scroll to bottom for latest convo
  setTimeout(() => {
    const scrollContainer = container.querySelector('#cell-container');
    if (scrollContainer) {
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }, 100);

  const input = container.querySelector('#cell-input') as HTMLTextAreaElement;
  const btn = container.querySelector('#btn-execute');

  // Auto-resize textarea
  input?.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
  });

  // Enter to send (Shift+Enter for newline)
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      btn?.dispatchEvent(new Event('click'));
    }
  });

  btn?.addEventListener('click', async () => {
    const question = input.value;
    if (!question || !activeId) return;
    
    input.value = '';
    input.style.height = 'auto';
    btn.setAttribute('disabled', 'true');
    btn.classList.add('opacity-50');

    // Create a temporary streaming bubble
    const cellContainer = container.querySelector('#cell-container');
    if (!cellContainer) return;

    // 1. Add user query bubble immediately
    const userBubble = document.createElement('div');
    userBubble.className = 'group animate-in fade-in slide-in-from-bottom-4 duration-500';
    userBubble.innerHTML = `
      <div class="flex items-center gap-4 mb-4">
         <div class="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center shrink-0 overflow-hidden border border-outline-variant/20">
            <span class="material-symbols-outlined text-outline text-sm" data-icon="person">person</span>
         </div>
         <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm">Operator</span>
      </div>
      <div class="pl-12">
        <div class="prose prose-invert max-w-none text-on-surface-variant leading-relaxed font-body-lg">
          ${renderMarkdown(question)}
        </div>
      </div>
    `;
    cellContainer.appendChild(userBubble);

    // 2. Add Kowalski streaming bubble
    const agentBubble = document.createElement('div');
    agentBubble.className = 'group animate-in fade-in slide-in-from-bottom-4 duration-500 mt-12';
    agentBubble.innerHTML = `
      <div class="flex items-center gap-4 mb-4">
         <div class="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center shrink-0 overflow-hidden border border-outline-variant/20">
            <img src="/src/assets/kowalski.png" class="w-full h-full object-cover" alt="Kowalski">
         </div>
         <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm">Kowalski</span>
      </div>
      <div class="pl-12">
        <div class="prose prose-invert max-w-none text-on-surface-variant leading-relaxed font-body-lg" id="streaming-content">
          <span class="inline-block w-1 h-4 bg-primary animate-pulse"></span>
        </div>
      </div>
    `;
    cellContainer.appendChild(agentBubble);
    cellContainer.scrollTop = cellContainer.scrollHeight;

    let fullText = "";
    const streamingContent = agentBubble.querySelector('#streaming-content');

    api.streamQuestion(activeId, question, 
      (token) => {
        fullText += token;
        if (streamingContent) {
          streamingContent.innerHTML = renderMarkdown(fullText) + '<span class="inline-block w-1 h-4 bg-primary animate-pulse ml-1"></span>';
          cellContainer.scrollTop = cellContainer.scrollHeight;
        }
      },
      async () => {
        // Complete
        if (streamingContent) {
          streamingContent.innerHTML = renderMarkdown(fullText);
        }
        btn.removeAttribute('disabled');
        btn.classList.remove('opacity-50');
        // Refresh to get official logs and IDs
        const newLogs = await api.listLogs(activeId);
        store.setLogs(newLogs);
      },
      (err) => {
        console.error('Streaming error', err);
        btn.removeAttribute('disabled');
        btn.classList.remove('opacity-50');
      }
    );
  });

  // Follow-up question clicks
  container.querySelectorAll('.followup-question-btn').forEach(fBtn => {
    fBtn.addEventListener('click', () => {
      const question = fBtn.getAttribute('data-question');
      if (!question) return;
      if (input) {
        input.value = question;
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
        btn?.dispatchEvent(new Event('click'));
      }
    });
  });

  return container;
}
