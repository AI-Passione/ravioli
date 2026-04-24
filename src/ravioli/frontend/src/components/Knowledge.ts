export function renderKnowledge() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 h-full overflow-hidden bg-surface relative flex items-center justify-center';

  container.innerHTML = `
    <div class="cinematic-vignette absolute inset-0 z-0"></div>
    
    <div class="max-w-2xl text-center space-y-8 animate-in fade-in zoom-in duration-1000 z-10 p-12 glass-panel rounded-[3rem] border-primary/10">
      <div class="w-24 h-24 rounded-[2rem] bg-primary/10 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-primary/20">
        <span class="material-symbols-outlined text-5xl text-primary" data-icon="local_library">local_library</span>
      </div>
      
      <div class="space-y-4">
        <h2 class="text-4xl font-headline-lg text-white tracking-tight">Knowledge Base</h2>
        <p class="text-on-surface-variant font-body-lg leading-relaxed">
          The sanctuary for in-house business domain intelligence. 
          Establish your analytical foundation by codifying domain expertise.
        </p>
      </div>

      <div class="pt-8 flex flex-col items-center gap-4">
        <div class="px-6 py-3 rounded-full bg-surface-container-high border border-outline-variant/30 flex items-center gap-3">
          <div class="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
          <span class="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">Synchronizing Domain Soul...</span>
        </div>
        <p class="text-[10px] text-outline uppercase tracking-[0.3em] opacity-50">Coming Soon to Studio Noir</p>
      </div>
    </div>
  `;

  return container;
}
