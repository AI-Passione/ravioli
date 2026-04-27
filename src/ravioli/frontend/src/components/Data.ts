import { store } from '../store';
import { api } from '../services/api';
import { formatBytes } from '../utils/formatters';

export function renderData() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 h-full overflow-y-auto bg-surface flex flex-col p-8 pt-12 relative';

  const files = store.getUploadedFiles();

  container.innerHTML = `
    <div class="max-w-6xl mx-auto w-full pb-20">
      <header class="mb-12 flex items-end justify-between">
        <div>
          <h1 class="text-4xl font-medium tracking-tight text-neutral-100 mb-2">Data Sources</h1>
          <p class="text-neutral-500 max-w-2xl">Manage your analytical assets. Ingested data is automatically synced with DuckDB.</p>
        </div>
        <button id="btn-add-source" class="px-6 py-3 rounded-2xl bg-primary text-on-primary font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 flex items-center gap-2 group">
          <span class="material-symbols-outlined group-hover:rotate-90 transition-transform">add</span>
          Add New Source
        </button>
      </header>

      <!-- Assets Table -->
      <div class="bg-surface-container-low rounded-3xl overflow-hidden border border-outline/10 shadow-2xl">
        <div class="px-8 py-6 border-b border-outline/10 flex items-center justify-between bg-surface-container-low/50 backdrop-blur-sm sticky top-0 z-10">
          <h2 class="text-lg font-medium text-neutral-200">Ingested Assets</h2>
          <span class="text-[10px] text-neutral-500 uppercase tracking-[0.2em]">${files.length} Total Assets</span>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="text-[10px] uppercase tracking-[0.2em] text-neutral-500 border-b border-outline/5">
                <th class="px-8 py-4 font-medium">Type</th>
                <th class="px-8 py-4 font-medium">Asset Name</th>
                <th class="px-8 py-4 font-medium">Description</th>
                <th class="px-8 py-4 font-medium">DuckDB Table</th>
                <th class="px-8 py-4 font-medium">Rows</th>
                <th class="px-8 py-4 font-medium">Status</th>
                <th class="px-8 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline/5">
              ${files.length === 0 ? `
                <tr>
                  <td colspan="7" class="px-8 py-20 text-center">
                    <div class="flex flex-col items-center justify-center">
                      <div class="w-16 h-16 rounded-2xl bg-surface-container-highest flex items-center justify-center mb-4 opacity-50">
                        <span class="material-symbols-outlined text-3xl">database_off</span>
                      </div>
                      <p class="text-neutral-500 italic">No assets ingested yet. Click "Add New Source" to get started.</p>
                    </div>
                  </td>
                </tr>
              ` : files.map(file => `
                <tr class="hover:bg-white/[0.02] transition-colors group">
                  <td class="px-8 py-5">
                    <div class="w-10 h-10 rounded-xl bg-surface-container-highest flex items-center justify-center border border-outline/5">
                      <span class="material-symbols-outlined text-lg ${file.source_type === 'wfs' ? 'text-primary' : 'text-neutral-400'}">
                        ${file.source_type === 'wfs' ? 'api' : 'description'}
                      </span>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    <div class="flex flex-col">
                      <div class="flex items-center gap-2">
                        <span class="text-neutral-200 font-medium">${file.original_filename}</span>
                        ${file.has_pii ? `
                          <span class="pii-badge inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-500 text-[9px] font-bold uppercase tracking-wider border border-amber-500/20 group/pii" data-id="${file.id}" title="Likely contains PII">
                            PII
                            <button class="btn-dismiss-pii hover:text-amber-300 transition-colors opacity-0 group-hover/pii:opacity-100 transition-opacity">
                              <span class="material-symbols-outlined text-[10px]">close</span>
                            </button>
                          </span>
                        ` : ''}
                      </div>
                      <span class="text-[10px] text-neutral-500 font-mono mt-0.5">${file.source_type === 'wfs' ? 'WFS API' : 'CSV File'} • ${formatBytes(file.size_bytes)}</span>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    <div class="desc-container flex items-center gap-2 group/desc max-w-xs w-full" data-id="${file.id}">
                      <span class="desc-text text-neutral-400 text-sm truncate cursor-pointer hover:text-neutral-200 transition-colors flex-1" title="${file.description || ''}" data-desc="${file.description || ''}">${file.description || '<span class="italic opacity-30">Add description...</span>'}</span>
                      <input type="text" class="desc-input hidden w-full bg-surface-container-highest border border-primary/30 rounded px-2 py-1 text-sm text-neutral-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all" value="${file.description || ''}" placeholder="Enter description..." />
                      <div class="flex items-center gap-1 opacity-0 group-hover/desc:opacity-100 transition-opacity">
                        <button class="btn-generate-desc p-1 rounded-md hover:bg-primary/10 text-primary/70 hover:text-primary transition-all flex-shrink-0" title="AI Generate Description">
                          <span class="material-symbols-outlined text-[16px]">auto_awesome</span>
                        </button>
                        <button class="btn-edit-desc p-1 rounded-md hover:bg-white/10 text-neutral-500 hover:text-primary transition-all flex-shrink-0" title="Edit Description">
                          <span class="material-symbols-outlined text-[16px]">edit</span>
                        </button>
                      </div>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    <code class="px-2 py-1 rounded bg-surface-container-highest text-primary-fixed-dim text-xs font-mono border border-outline/5">${file.schema_name}.${file.table_name}</code>
                  </td>
                  <td class="px-8 py-5 text-neutral-300 font-medium">
                    ${file.row_count ? file.row_count.toLocaleString() : '--'}
                  </td>
                  <td class="px-8 py-5">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] uppercase tracking-wider font-bold ${
                      file.status === 'completed' ? 'bg-green-500/10 text-green-400' : 
                      file.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                    }">
                      <span class="w-1.5 h-1.5 rounded-full ${file.status === 'completed' ? 'bg-green-400' : file.status === 'failed' ? 'bg-red-400' : 'bg-yellow-400'} ${file.status !== 'completed' ? 'animate-pulse' : ''}"></span>
                      ${file.status}
                    </span>
                  </td>
                  <td class="px-8 py-5 text-right flex justify-end gap-2">
                    <button class="btn-inspect p-2 rounded-lg hover:bg-primary/10 text-neutral-400 hover:text-primary transition-all" data-table="${file.schema_name}.${file.table_name}" data-filename="${file.original_filename}" title="Preview">
                      <span class="material-symbols-outlined">visibility</span>
                    </button>
                    <button class="btn-delete p-2 rounded-lg hover:bg-red-500/10 text-neutral-400 hover:text-red-400 transition-all" data-id="${file.id}" title="Delete">
                      <span class="material-symbols-outlined">delete</span>
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add Source Modal -->
    <div id="add-source-modal" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-md hidden opacity-0 transition-opacity duration-300">
      <div class="bg-surface-container rounded-[2rem] w-full max-w-2xl flex flex-col shadow-2xl border border-outline/10 translate-y-4 transition-transform duration-300 overflow-hidden">
        <header class="px-8 py-6 border-b border-outline/10 flex items-center justify-between bg-surface-container-high/50">
          <div>
            <h2 class="text-xl font-medium text-neutral-100">Add New Data Source</h2>
            <p id="modal-step-subtitle" class="text-xs text-neutral-500 uppercase tracking-widest mt-1">Select ingestion method</p>
          </div>
          <button id="close-add-modal" class="p-2 rounded-full hover:bg-white/5 text-neutral-400 hover:text-white transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        
        <div id="add-modal-content" class="p-8">
          <!-- Step 1: Selection -->
          <div id="step-selection" class="grid grid-cols-2 gap-6">
            <div class="source-type-card p-8 rounded-3xl bg-surface-container-highest border border-outline/10 hover:border-primary/50 hover:bg-surface-container-highest/80 cursor-pointer transition-all group flex flex-col items-center text-center" data-type="wfs">
              <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-primary text-4xl">api</span>
              </div>
              <h3 class="text-lg font-medium text-neutral-100 mb-2">WFS API</h3>
              <p class="text-sm text-neutral-500">Connect to geospatial web feature services (Opendata, Geoserver)</p>
            </div>
            
            <div class="source-type-card p-8 rounded-3xl bg-surface-container-highest border border-outline/10 hover:border-primary/50 hover:bg-surface-container-highest/80 cursor-pointer transition-all group flex flex-col items-center text-center" data-type="csv">
              <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-primary text-4xl">upload_file</span>
              </div>
              <h3 class="text-lg font-medium text-neutral-100 mb-2">Flat File</h3>
              <p class="text-sm text-neutral-500">Upload CSV files from your local machine</p>
            </div>
          </div>

          <!-- Step 2: WFS Form -->
          <div id="step-wfs" class="hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div class="space-y-6">
              <div class="relative">
                <label class="text-[10px] uppercase tracking-widest text-neutral-500 mb-2 block">Service URL</label>
                <input type="text" id="wfs-url" placeholder="https://..." 
                  class="w-full bg-surface-container-highest border border-outline/20 rounded-2xl px-6 py-4 text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-primary/50 transition-all" />
              </div>
              
              <div id="wfs-ingest-controls" class="flex justify-end pt-4 border-t border-outline/5">
                <button id="btn-ingest-wfs" class="px-8 py-3 rounded-2xl bg-primary text-on-primary font-medium hover:bg-primary/90 transition-all flex items-center gap-2 group">
                  Start Ingestion
                  <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
                </button>
              </div>
            </div>
            <button class="btn-back mt-8 text-neutral-500 hover:text-neutral-300 flex items-center gap-2 text-sm transition-colors">
              <span class="material-symbols-outlined text-lg">arrow_back</span>
              Back to Selection
            </button>
          </div>

          <!-- Step 2: CSV Form -->
          <div id="step-csv" class="hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div id="drop-zone" class="border-2 border-dashed border-outline/20 rounded-3xl p-12 flex flex-col items-center justify-center bg-surface-container-highest hover:bg-surface-container hover:border-primary/50 transition-all cursor-pointer group relative overflow-hidden">
              <div id="drop-zone-content" class="flex flex-col items-center justify-center transition-opacity duration-300">
                <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-primary text-3xl">upload_file</span>
                </div>
                <h3 class="text-xl font-medium text-neutral-200 mb-2">Drop your CSV here</h3>
                <p class="text-neutral-500 text-sm">or click to browse your files</p>
              </div>
              <div id="drop-zone-loading" class="absolute inset-0 flex flex-col items-center justify-center bg-surface-container/90 backdrop-blur-sm opacity-0 pointer-events-none transition-opacity duration-300 z-10">
                <span class="material-symbols-outlined animate-spin text-primary text-4xl mb-4">sync</span>
                <p class="text-neutral-200 font-medium animate-pulse">Processing...</p>
              </div>
              <input type="file" id="file-input" class="hidden" accept=".csv">
            </div>
            <button class="btn-back mt-8 text-neutral-500 hover:text-neutral-300 flex items-center gap-2 text-sm transition-colors">
              <span class="material-symbols-outlined text-lg">arrow_back</span>
              Back to Selection
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <div id="preview-modal" class="fixed inset-0 z-[110] flex items-center justify-center p-8 bg-black/80 backdrop-blur-md hidden opacity-0 transition-opacity duration-300">
      <div class="bg-surface-container rounded-[2rem] w-full max-w-5xl h-[80vh] flex flex-col shadow-2xl border border-outline/10 translate-y-4 transition-transform duration-300 overflow-hidden">
        <header class="px-8 py-6 border-b border-outline/10 flex items-center justify-between">
          <div>
            <h2 id="modal-title" class="text-xl font-medium text-neutral-100">Data Preview</h2>
            <p id="modal-subtitle" class="text-xs text-neutral-500 uppercase tracking-widest mt-1">Showing first 10 rows</p>
          </div>
          <button id="close-preview-modal" class="p-2 rounded-full hover:bg-white/5 text-neutral-400 hover:text-white transition-colors">
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div id="modal-content" class="flex-1 overflow-auto p-8">
          <div class="flex items-center justify-center h-full">
            <span class="material-symbols-outlined animate-spin text-primary">sync</span>
          </div>
        </div>
      </div>
    </div>
  `;

  // --- Modal Logic ---
  const addModal = container.querySelector('#add-source-modal') as HTMLElement;
  const btnAddSource = container.querySelector('#btn-add-source');
  const closeAddModal = container.querySelector('#close-add-modal');
  const stepSelection = container.querySelector('#step-selection') as HTMLElement;
  const stepWfs = container.querySelector('#step-wfs') as HTMLElement;
  const stepCsv = container.querySelector('#step-csv') as HTMLElement;
  const stepSubtitle = container.querySelector('#modal-step-subtitle') as HTMLElement;
  const sourceTypeCards = container.querySelectorAll('.source-type-card');
  const btnBacks = container.querySelectorAll('.btn-back');

  const showStep = (step: 'selection' | 'wfs' | 'csv') => {
    stepSelection.classList.toggle('hidden', step !== 'selection');
    stepWfs.classList.toggle('hidden', step !== 'wfs');
    stepCsv.classList.toggle('hidden', step !== 'csv');
    
    if (step === 'selection') stepSubtitle.textContent = 'Select ingestion method';
    else if (step === 'wfs') stepSubtitle.textContent = 'Configure WFS API Source';
    else if (step === 'csv') stepSubtitle.textContent = 'Upload CSV Data';
  };

  btnAddSource?.addEventListener('click', () => {
    addModal.classList.remove('hidden');
    setTimeout(() => {
      addModal.classList.remove('opacity-0');
      addModal.querySelector('div')?.classList.remove('translate-y-4');
    }, 10);
    showStep('selection');
  });

  const hideAddModal = () => {
    addModal.classList.add('opacity-0');
    addModal.querySelector('div')?.classList.add('translate-y-4');
    setTimeout(() => addModal.classList.add('hidden'), 300);
  };

  closeAddModal?.addEventListener('click', hideAddModal);
  
  sourceTypeCards.forEach(card => {
    card.addEventListener('click', () => {
      const type = card.getAttribute('data-type');
      showStep(type as any);
    });
  });

  btnBacks.forEach(btn => {
    btn.addEventListener('click', () => showStep('selection'));
  });

  // --- WFS Ingestion Logic ---
  const wfsUrlInput = container.querySelector('#wfs-url') as HTMLInputElement;
  const ingestBtn = container.querySelector('#btn-ingest-wfs') as HTMLButtonElement;

  ingestBtn?.addEventListener('click', async () => {
    const url = wfsUrlInput.value.trim();
    if (!url) return;

    ingestBtn.innerHTML = '<span class="material-symbols-outlined animate-spin text-sm">sync</span> Starting...';
    ingestBtn.disabled = true;

    try {
      // 1. Automatically determine the layer
      const layers = await api.getWFSLayers(url);
      if (layers.length === 0) {
        throw new Error('No layers found at this URL.');
      }
      const primaryLayer = layers[0].name;
      
      // 2. Fire ingestion — backend returns immediately with 'pending' status
      const result = await api.ingestWFSLayer(url, primaryLayer);
      
      // 3. Close modal right away — user can do other things
      hideAddModal();
      refreshFiles();

      // 4. Poll in the background until completed or failed
      if (result.status === 'pending') {
        const pollInterval = setInterval(async () => {
          try {
            const files = await api.listFiles();
            const updated = files.find(f => f.id === result.id);
            if (updated && updated.status !== 'pending') {
              clearInterval(pollInterval);
              refreshFiles();
            }
          } catch {
            clearInterval(pollInterval);
          }
        }, 3000);
      }
    } catch (err: any) {
      alert(`Failed to start ingestion: ${err.message || err}`);
    } finally {
      ingestBtn.innerHTML = 'Start Ingestion <span class="material-symbols-outlined">arrow_forward</span>';
      ingestBtn.disabled = false;
    }
  });

  // --- CSV Upload Logic ---
  const dropZone = container.querySelector('#drop-zone');
  const fileInput = container.querySelector('#file-input') as HTMLInputElement;
  
  dropZone?.addEventListener('click', () => fileInput.click());
  fileInput?.addEventListener('change', async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) await handleUpload(file);
  });

  async function handleUpload(file: File) {
    const dropZoneContent = container.querySelector('#drop-zone-content');
    const dropZoneLoading = container.querySelector('#drop-zone-loading');
    dropZoneContent?.classList.add('opacity-0');
    dropZoneLoading?.classList.remove('opacity-0', 'pointer-events-none');

    try {
      const result = await api.uploadFile(file);
      if (result.is_duplicate) alert('Duplicate Data Detected: Already uploaded.');
      hideAddModal();
      refreshFiles();
    } catch (err) {
      alert('Upload failed.');
    } finally {
      dropZoneContent?.classList.remove('opacity-0');
      dropZoneLoading?.classList.add('opacity-0', 'pointer-events-none');
    }
  }

  // --- General Table Logic ---
  const refreshFiles = async () => {
    const updatedFiles = await api.listFiles();
    store.setUploadedFiles(updatedFiles);
    // Note: In this pure vanilla setup, the store update triggers a re-render 
    // of the app via the subscription in main.ts.
  };

  container.querySelectorAll('.btn-inspect').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tableName = btn.getAttribute('data-table');
      const filename = btn.getAttribute('data-filename');
      if (tableName) showPreview(tableName, filename || tableName);
    });
  });

  container.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', async () => {
      const fileId = btn.getAttribute('data-id');
      if (fileId && confirm('Delete this data?')) {
        await api.deleteFile(fileId);
        refreshFiles();
      }
    });
  });

  // Preview Logic
  const previewModal = container.querySelector('#preview-modal') as HTMLElement;
  const modalContent = container.querySelector('#modal-content') as HTMLElement;
  const modalTitle = container.querySelector('#modal-title') as HTMLElement;
  const closePreviewModal = container.querySelector('#close-preview-modal');

  async function showPreview(tableName: string, filename: string) {
    modalTitle.textContent = filename;
    previewModal.classList.remove('hidden');
    setTimeout(() => {
      previewModal.classList.remove('opacity-0');
      previewModal.querySelector('div')?.classList.remove('translate-y-4');
    }, 10);

    try {
      const data = await api.getPreview(tableName);
      if (data.length === 0) {
        modalContent.innerHTML = '<div class="text-center py-20 italic">No data found.</div>';
        return;
      }
      const headers = Object.keys(data[0]);
      modalContent.innerHTML = `
        <div class="overflow-x-auto rounded-xl border border-outline/5">
          <table class="w-full text-left border-collapse bg-surface-container-lowest">
            <thead>
              <tr class="bg-surface-container-highest">
                ${headers.map(h => `<th class="px-4 py-3 text-[10px] uppercase tracking-widest text-neutral-400 border-b border-outline/10">${h}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${data.map(row => `
                <tr class="border-b border-outline/5 hover:bg-white/[0.02]">
                  ${headers.map(h => `<td class="px-4 py-3 text-sm text-neutral-300 font-mono whitespace-nowrap">${row[h]}</td>`).join('')}
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      modalContent.innerHTML = `<div class="text-center text-red-400 py-20">Load failed.</div>`;
    }
  }

  const hidePreviewModal = () => {
    previewModal.classList.add('opacity-0');
    previewModal.querySelector('div')?.classList.add('translate-y-4');
    setTimeout(() => previewModal.classList.add('hidden'), 300);
  };
  closePreviewModal?.addEventListener('click', hidePreviewModal);

  // Description Editing
  container.querySelectorAll('.desc-container').forEach(descContainer => {
    const textSpan = descContainer.querySelector('.desc-text') as HTMLSpanElement;
    const inputEl = descContainer.querySelector('.desc-input') as HTMLInputElement;
    const editBtn = descContainer.querySelector('.btn-edit-desc') as HTMLButtonElement;
    const generateBtn = descContainer.querySelector('.btn-generate-desc') as HTMLButtonElement;
    const fileId = descContainer.getAttribute('data-id');

    const startEditing = () => {
      textSpan.classList.add('hidden');
      editBtn.closest('div')?.classList.add('hidden');
      inputEl.classList.remove('hidden');
      inputEl.focus();
    };

    const stopEditing = async (save: boolean) => {
      if (inputEl.classList.contains('hidden')) return;
      inputEl.classList.add('hidden');
      textSpan.classList.remove('hidden');
      editBtn.closest('div')?.classList.remove('hidden');
      if (save && fileId) {
        const newDesc = inputEl.value.trim();
        if (newDesc !== textSpan.getAttribute('data-desc')) {
          await api.updateFileDescription(fileId, newDesc);
          refreshFiles();
        }
      }
    };

    generateBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!fileId) return;
      generateBtn.innerHTML = '<span class="material-symbols-outlined text-[16px] animate-spin">sync</span>';
      try {
        await api.generateFileDescription(fileId);
        refreshFiles();
      } catch (err) {
        alert('Generation failed.');
        generateBtn.innerHTML = 'auto_awesome';
      }
    });

    textSpan.addEventListener('click', startEditing);
    editBtn.addEventListener('click', startEditing);
    inputEl.addEventListener('blur', () => stopEditing(true));
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') stopEditing(true);
      else if (e.key === 'Escape') stopEditing(false);
    });
  });

  // PII Tag Dismissal
  container.querySelectorAll('.btn-dismiss-pii').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const badge = btn.closest('.pii-badge') as HTMLElement;
      const fileId = badge.getAttribute('data-id');
      if (fileId && confirm('Mark this as false positive? The PII tag will be removed.')) {
        try {
          await api.togglePIITag(fileId, false);
          refreshFiles();
        } catch (err) {
          alert('Failed to update PII status.');
        }
      }
    });
  });

  return container;
}
