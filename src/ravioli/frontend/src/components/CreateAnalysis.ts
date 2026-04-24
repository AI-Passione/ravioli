import { store } from '../store';
import { api } from '../services/api';

type CreationMode = 'select' | 'quick' | 'deep';

export function renderCreateAnalysis() {
  let mode: CreationMode = 'select';
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 relative overflow-hidden bg-background h-screen flex flex-col items-center justify-center';

  function updateUI() {
    container.innerHTML = `
      <!-- Cinematic Vignette Overlay -->
      <div class="absolute inset-0 cinematic-vignette"></div>

      <div class="max-w-4xl w-full space-y-12 relative z-10 px-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div class="text-center space-y-4">
          <h2 class="text-5xl font-display-lg text-on-surface tracking-tight">
            ${mode === 'select' ? 'Choose Your Path' : mode === 'quick' ? 'Quick Insight' : 'Deep Dive'}
          </h2>
          <p class="font-label-sm text-label-sm tracking-[0.4em] text-tertiary-fixed-dim uppercase">
            ${mode === 'select' ? 'Select the level of orchestration required.' : 'Initialize your parameters for processing.'}
          </p>
        </div>

        ${mode === 'select' ? renderSelection() : mode === 'quick' ? renderQuick() : renderDeep()}
        
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

    attachEventListeners();
  }

  function renderSelection() {
    return `
      <div class="grid grid-cols-2 gap-8">
        <!-- Quick Insight Card -->
        <button id="mode-quick" class="glass-panel p-10 rounded-3xl space-y-6 text-left group hover:border-primary-fixed-dim/40 transition-all hover:-translate-y-1">
          <div class="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
            <span class="material-symbols-outlined text-3xl" data-icon="bolt">bolt</span>
          </div>
          <div class="space-y-2">
            <h3 class="text-2xl font-headline-sm text-white">Quick Insight</h3>
            <p class="text-on-surface-variant text-sm leading-relaxed opacity-70">
              Upload a CSV and get an instant AI-powered executive summary. Perfect for vibe-checking new data streams.
            </p>
          </div>
          <div class="flex items-center gap-2 text-primary text-[10px] font-label-sm uppercase tracking-widest pt-4">
            <span>Fast Track</span>
            <span class="material-symbols-outlined text-sm" data-icon="arrow_forward">arrow_forward</span>
          </div>
        </button>

        <!-- Deep Dive Card -->
        <button id="mode-deep" class="glass-panel p-10 rounded-3xl space-y-6 text-left group hover:border-secondary-fixed-dim/40 transition-all hover:-translate-y-1">
          <div class="w-12 h-12 rounded-2xl bg-secondary/10 flex items-center justify-center text-secondary group-hover:scale-110 transition-transform">
            <span class="material-symbols-outlined text-3xl" data-icon="biotech">biotech</span>
          </div>
          <div class="space-y-2">
            <h3 class="text-2xl font-headline-sm text-white">Deep Dive</h3>
            <p class="text-on-surface-variant text-sm leading-relaxed opacity-70">
              Create a full investigation notebook. Query, transform, and visualize with the complete Ravioli toolset.
            </p>
          </div>
          <div class="flex items-center gap-2 text-secondary text-[10px] font-label-sm uppercase tracking-widest pt-4">
            <span>Orchestration</span>
            <span class="material-symbols-outlined text-sm" data-icon="arrow_forward">arrow_forward</span>
          </div>
        </button>
      </div>
      
      <div class="flex justify-center pt-8">
        <button id="cancel-create" class="text-sm font-label-sm text-outline hover:text-white uppercase tracking-widest transition-colors">
          Abort Mission
        </button>
      </div>
    `;
  }

  function renderQuick() {
    return `
      <div class="glass-panel p-10 rounded-3xl space-y-8 max-w-xl mx-auto w-full">
        <div id="drop-zone" class="border-2 border-dashed border-outline-variant/30 rounded-2xl p-12 text-center space-y-4 hover:border-primary-fixed-dim/50 transition-colors cursor-pointer group">
          <input type="file" id="file-input" class="hidden" accept=".csv" />
          <div class="w-16 h-16 rounded-full bg-surface-container-highest flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
            <span class="material-symbols-outlined text-3xl text-outline" data-icon="upload_file">upload_file</span>
          </div>
          <div class="space-y-1">
            <p class="text-white font-medium">Drop your CSV here</p>
            <p class="text-xs text-on-surface-variant opacity-60">or click to browse local files</p>
          </div>
        </div>

        <div id="processing-state" class="hidden space-y-6 py-8 text-center">
          <div class="relative w-20 h-20 mx-auto">
            <div class="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
            <div class="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div class="space-y-2">
            <p class="text-xl font-headline-sm text-white animate-pulse">Syncing Neural Link...</p>
            <p class="text-xs text-on-surface-variant uppercase tracking-widest opacity-60">Generating Executive Summary</p>
          </div>
        </div>

        <div class="flex items-center justify-between pt-4">
          <button id="back-to-select" class="text-sm font-label-sm text-outline hover:text-white uppercase tracking-widest transition-colors">
            Back
          </button>
          <p class="text-[10px] text-outline uppercase tracking-widest opacity-40">Local LLM Node Ready</p>
        </div>
      </div>
    `;
  }

  function renderDeep() {
    return `
      <div class="glass-panel p-10 rounded-3xl space-y-8 max-w-xl mx-auto w-full">
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
          <button id="back-to-select" class="text-sm font-label-sm text-outline hover:text-white uppercase tracking-widest transition-colors">
            Back
          </button>
          <button id="confirm-create" class="btn-primary flex items-center gap-3 group">
            <span>Initialize</span>
            <span class="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform" data-icon="rocket_launch">rocket_launch</span>
          </button>
        </div>
      </div>
    `;
  }

  function attachEventListeners() {
    container.querySelector('#cancel-create')?.addEventListener('click', () => {
      store.setCurrentView('dashboard');
    });

    container.querySelector('#back-to-select')?.addEventListener('click', () => {
      mode = 'select';
      updateUI();
    });

    container.querySelector('#mode-quick')?.addEventListener('click', () => {
      mode = 'quick';
      updateUI();
    });

    container.querySelector('#mode-deep')?.addEventListener('click', () => {
      mode = 'deep';
      updateUI();
    });

    // Quick Insight Upload
    const dropZone = container.querySelector('#drop-zone');
    const fileInput = container.querySelector('#file-input') as HTMLInputElement;

    dropZone?.addEventListener('click', () => fileInput.click());
    
    fileInput?.addEventListener('change', async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) handleFileUpload(file);
    });

    dropZone?.addEventListener('dragover', (e: any) => {
      e.preventDefault();
      dropZone.classList.add('border-primary-fixed-dim');
    });

    dropZone?.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-primary-fixed-dim');
    });

    dropZone?.addEventListener('drop', (e: any) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFileUpload(file);
    });

    // Deep Dive Confirm
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
      btn.innerHTML = '<span>Initializing...</span>';

      try {
        const newAnalysis = await api.createAnalysis({ 
          title, 
          description: descInput.value.trim() 
        });
        const currentAnalyses = store.getAnalyses();
        store.setAnalyses([newAnalysis, ...currentAnalyses]);
        store.setActiveAnalysisId(newAnalysis.id);
      } catch (err) {
        console.error('Failed to create analysis', err);
        btn.disabled = false;
        btn.innerHTML = '<span>Initialize</span>';
      }
    });
  }

  async function handleFileUpload(file: File) {
    if (!file.name.endsWith('.csv')) {
      alert('Please upload a CSV file.');
      return;
    }

    const dropZone = container.querySelector('#drop-zone');
    const processingState = container.querySelector('#processing-state');
    const backBtn = container.querySelector('#back-to-select');

    dropZone?.classList.add('hidden');
    processingState?.classList.remove('hidden');
    if (backBtn) (backBtn as HTMLButtonElement).disabled = true;

    try {
      const result = await api.generateQuickInsight(file);
      // Fetch updated list of analyses to include the new one
      const analyses = await api.listAnalyses();
      store.setAnalyses(analyses);
      store.setActiveAnalysisId(result.analysis_id);
    } catch (err) {
      console.error('Failed to generate quick insight', err);
      alert('Failed to process data. Please try again.');
      dropZone?.classList.remove('hidden');
      processingState?.classList.add('hidden');
      if (backBtn) (backBtn as HTMLButtonElement).disabled = false;
    }
  }

  updateUI();
  return container;
}
