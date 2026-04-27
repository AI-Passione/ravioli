import { store } from '../store';
import { api } from '../services/api';
import { formatBytes } from '../utils/formatters';

export function renderData() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 h-full overflow-hidden bg-surface flex flex-col p-8 pt-12 relative';

  const files = store.getUploadedFiles();

  container.innerHTML = `
    <div class="max-w-6xl mx-auto w-full">
      <header class="mb-12">
        <h1 class="text-4xl font-medium tracking-tight text-neutral-100 mb-2">Data</h1>
        <p class="text-neutral-500 max-w-2xl">Manage and inspect your ingested data assets. All files are automatically synced with DuckDB.</p>
      </header>

      <!-- Upload Zone -->
      <div class="mb-12">
        <div id="drop-zone" class="border-2 border-dashed border-outline/30 rounded-3xl p-12 flex flex-col items-center justify-center bg-surface-container-low hover:bg-surface-container hover:border-primary/50 transition-all cursor-pointer group relative overflow-hidden">
          <div id="drop-zone-content" class="flex flex-col items-center justify-center transition-opacity duration-300 w-full h-full">
            <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-primary text-3xl">upload_file</span>
            </div>
            <h3 class="text-xl font-medium text-neutral-200 mb-2">Drop your CSV here</h3>
            <p class="text-neutral-500 text-sm">or click to browse your files</p>
          </div>
          <div id="drop-zone-loading" class="absolute inset-0 flex flex-col items-center justify-center bg-surface-container/90 backdrop-blur-sm opacity-0 pointer-events-none transition-opacity duration-300 z-10">
            <span class="material-symbols-outlined animate-spin text-primary text-4xl mb-4">sync</span>
            <p class="text-neutral-200 font-medium animate-pulse">Uploading and processing...</p>
          </div>
          <input type="file" id="file-input" class="hidden" accept=".csv">
        </div>
      </div>

      <!-- API Ingestion Section -->
      <div class="mb-12">
        <div class="bg-surface-container-low rounded-3xl p-8 border border-outline/10 shadow-xl">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary text-2xl">api</span>
            </div>
            <div>
              <h2 class="text-xl font-medium text-neutral-100">API Integration</h2>
              <p class="text-xs text-neutral-500 uppercase tracking-widest mt-1">Ingest data from WFS services</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div class="md:col-span-8 relative">
              <input type="text" id="wfs-url" placeholder="Enter WFS Service URL (e.g., https://gdi.berlin.de/services/wfs/gewerbedaten)" 
                class="w-full bg-surface-container-highest border border-outline/20 rounded-2xl px-6 py-4 text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-primary/50 transition-all pr-32"
                value="https://gdi.berlin.de/services/wfs/gewerbedaten" />
              <button id="btn-fetch-layers" class="absolute right-2 top-2 bottom-2 px-6 rounded-xl bg-primary text-on-primary font-medium hover:bg-primary/90 transition-all flex items-center gap-2">
                <span class="material-symbols-outlined text-sm">sync</span>
                Fetch
              </button>
            </div>
            <div class="md:col-span-4">
               <select id="wfs-layer-select" disabled class="w-full h-full bg-surface-container-highest border border-outline/20 rounded-2xl px-6 py-4 text-neutral-200 focus:outline-none focus:border-primary/50 transition-all appearance-none disabled:opacity-50 disabled:cursor-not-allowed">
                <option value="">Select a layer...</option>
              </select>
            </div>
          </div>

          <div id="wfs-ingest-container" class="mt-6 flex items-center justify-between opacity-0 pointer-events-none transition-all duration-300 translate-y-2">
            <div class="flex items-center gap-4">
              <div class="flex flex-col">
                <label class="text-[10px] uppercase tracking-widest text-neutral-500 mb-1">Max Rows</label>
                <input type="number" id="wfs-count" value="1000" step="100" min="1" max="50000" class="w-32 bg-surface-container-highest border border-outline/20 rounded-xl px-4 py-2 text-neutral-200 focus:outline-none focus:border-primary/50" />
              </div>
            </div>
            <button id="btn-ingest-wfs" class="px-8 py-3 rounded-2xl bg-primary/20 text-primary border border-primary/30 font-medium hover:bg-primary hover:text-on-primary transition-all flex items-center gap-3 group">
              <span>Start Ingestion</span>
              <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Files List -->
      <div class="bg-surface-container-low rounded-3xl overflow-hidden border border-outline/10 shadow-2xl">
        <div class="px-8 py-6 border-b border-outline/10 flex items-center justify-between bg-surface-container-low/50 backdrop-blur-sm sticky top-0 z-10">
          <h2 class="text-lg font-medium text-neutral-200">Ingested Assets</h2>
          <span class="text-xs text-neutral-500 uppercase tracking-widest">${files.length} Assets</span>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="text-[10px] uppercase tracking-[0.2em] text-neutral-500 border-b border-outline/5">
                <th class="px-8 py-4 font-medium">Asset Name</th>
                <th class="px-8 py-4 font-medium">Description</th>
                <th class="px-8 py-4 font-medium">DuckDB Table</th>
                <th class="px-8 py-4 font-medium">Rows</th>
                <th class="px-8 py-4 font-medium">Size</th>
                <th class="px-8 py-4 font-medium">Status</th>
                <th class="px-8 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline/5">
              ${files.length === 0 ? `
                <tr>
                  <td colspan="6" class="px-8 py-12 text-center text-neutral-500 italic">No assets ingested yet.</td>
                </tr>
              ` : files.map(file => `
                <tr class="hover:bg-white/[0.02] transition-colors group">
                  <td class="px-8 py-5">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
                        <span class="material-symbols-outlined text-neutral-400 group-hover:text-primary transition-colors text-lg">description</span>
                      </div>
                      <span class="text-neutral-200 font-medium">${file.original_filename}</span>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    <div class="desc-container flex items-center gap-2 group/desc max-w-xs w-full" data-id="${file.id}">
                      <span class="desc-text text-neutral-400 text-sm truncate cursor-pointer hover:text-neutral-200 transition-colors flex-1" title="${file.description || ''}" data-desc="${file.description || ''}">${file.description || '<span class="italic opacity-50">Add description...</span>'}</span>
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
                    <code class="px-2 py-1 rounded bg-surface-container-highest text-primary-fixed-dim text-xs font-mono">${file.table_name}</code>
                  </td>
                  <td class="px-8 py-5 text-neutral-300 font-medium">
                    ${file.row_count ? file.row_count.toLocaleString() : '--'}
                  </td>
                  <td class="px-8 py-5 text-neutral-400 text-sm">
                    ${formatBytes(file.size_bytes)}
                  </td>
                  <td class="px-8 py-5">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] uppercase tracking-wider font-bold ${
                      file.status === 'completed' ? 'bg-green-500/10 text-green-400' : 
                      file.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                    }">
                      <span class="w-1 h-1 rounded-full ${file.status === 'completed' ? 'bg-green-400' : file.status === 'failed' ? 'bg-red-400' : 'bg-yellow-400'} animate-pulse"></span>
                      ${file.status}
                    </span>
                  </td>
                  <td class="px-8 py-5 text-right flex justify-end gap-2">
                    <button class="btn-inspect p-2 rounded-lg hover:bg-primary/10 text-neutral-400 hover:text-primary transition-all" data-table="${file.table_name}" data-filename="${file.original_filename}" title="Preview">
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

    <!-- Preview Modal -->
    <div id="preview-modal" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/60 backdrop-blur-sm hidden opacity-0 transition-opacity duration-300">
      <div class="bg-surface-container rounded-3xl w-full max-w-5xl h-[80vh] flex flex-col shadow-2xl border border-outline/10 translate-y-4 transition-transform duration-300">
        <header class="px-8 py-6 border-b border-outline/10 flex items-center justify-between">
          <div>
            <h2 id="modal-title" class="text-xl font-medium text-neutral-100">Data Preview</h2>
            <p id="modal-subtitle" class="text-xs text-neutral-500 uppercase tracking-widest mt-1">Showing first 10 rows</p>
          </div>
          <button id="close-modal" class="p-2 rounded-full hover:bg-white/5 text-neutral-400 hover:text-white transition-colors">
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

  // Event Listeners
  const dropZone = container.querySelector('#drop-zone');
  const fileInput = container.querySelector('#file-input') as HTMLInputElement;
  const modal = container.querySelector('#preview-modal') as HTMLElement;
  const modalContent = container.querySelector('#modal-content') as HTMLElement;
  const modalTitle = container.querySelector('#modal-title') as HTMLElement;
  const closeModal = container.querySelector('#close-modal');

  // WFS Elements
  const wfsUrlInput = container.querySelector('#wfs-url') as HTMLInputElement;
  const fetchLayersBtn = container.querySelector('#btn-fetch-layers') as HTMLButtonElement;
  const layerSelect = container.querySelector('#wfs-layer-select') as HTMLSelectElement;
  const ingestContainer = container.querySelector('#wfs-ingest-container') as HTMLElement;
  const ingestBtn = container.querySelector('#btn-ingest-wfs') as HTMLButtonElement;
  const countInput = container.querySelector('#wfs-count') as HTMLInputElement;

  fetchLayersBtn?.addEventListener('click', async () => {
    const url = wfsUrlInput.value.trim();
    if (!url) return;

    const originalText = fetchLayersBtn.innerHTML;
    fetchLayersBtn.innerHTML = '<span class="material-symbols-outlined animate-spin text-sm">sync</span> Fetching...';
    fetchLayersBtn.disabled = true;

    try {
      const layers = await api.getWFSLayers(url);
      layerSelect.innerHTML = '<option value="">Select a layer...</option>' + 
        layers.map(l => `<option value="${l.name}">${l.title || l.name}</option>`).join('');
      layerSelect.disabled = false;
      alert('Layers fetched successfully!');
    } catch (err) {
      console.error('Fetch layers failed', err);
      alert('Failed to fetch layers. Please check the URL and ensure it is a valid WFS service.');
    } finally {
      fetchLayersBtn.innerHTML = originalText;
      fetchLayersBtn.disabled = false;
    }
  });

  layerSelect?.addEventListener('change', () => {
    if (layerSelect.value) {
      ingestContainer.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-2');
    } else {
      ingestContainer.classList.add('opacity-0', 'pointer-events-none', 'translate-y-2');
    }
  });

  ingestBtn?.addEventListener('click', async () => {
    const url = wfsUrlInput.value.trim();
    const layer = layerSelect.value;
    const count = parseInt(countInput.value) || 1000;

    if (!url || !layer) return;

    const originalText = ingestBtn.innerHTML;
    ingestBtn.innerHTML = '<span class="material-symbols-outlined animate-spin text-sm">sync</span> Ingesting...';
    ingestBtn.disabled = true;

    try {
      const result = await api.ingestWFSLayer(url, layer, count);
      if (result.status === 'completed') {
        alert(`Successfully ingested ${result.row_count} rows from ${layer}!`);
      } else if (result.status === 'failed') {
        alert(`Ingestion failed: ${result.error_message}`);
      }
      
      const updatedFiles = await api.listFiles();
      store.setUploadedFiles(updatedFiles);
    } catch (err) {
      console.error('Ingestion failed', err);
      alert('Failed to start ingestion.');
    } finally {
      ingestBtn.innerHTML = originalText;
      ingestBtn.disabled = false;
    }
  });

  dropZone?.addEventListener('click', () => fileInput.click());

  fileInput?.addEventListener('change', async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) {
      await handleUpload(file);
    }
  });

  dropZone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-primary', 'bg-surface-container');
  });

  dropZone?.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-primary', 'bg-surface-container');
  });

  dropZone?.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-primary', 'bg-surface-container');
    const file = (e as DragEvent).dataTransfer?.files[0];
    if (file && file.name.endsWith('.csv')) {
      await handleUpload(file);
    }
  });

  container.querySelectorAll('.btn-inspect').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tableName = btn.getAttribute('data-table');
      const filename = btn.getAttribute('data-filename');
      if (tableName) {
        showPreview(tableName, filename || tableName);
      }
    });
  });

  container.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', async () => {
      const fileId = btn.getAttribute('data-id');
      if (fileId && confirm('Are you sure you want to delete this data? This will remove it from DuckDB and cannot be undone.')) {
        try {
          await api.deleteFile(fileId);
          const updatedFiles = await api.listFiles();
          store.setUploadedFiles(updatedFiles);
        } catch (err) {
          console.error('Delete failed', err);
          alert('Failed to delete file.');
        }
      }
    });
  });

  container.querySelectorAll('.desc-container').forEach(descContainer => {
    const textSpan = descContainer.querySelector('.desc-text') as HTMLSpanElement;
    const inputEl = descContainer.querySelector('.desc-input') as HTMLInputElement;
    const editBtn = descContainer.querySelector('.btn-edit-desc') as HTMLButtonElement;
    const generateBtn = descContainer.querySelector('.btn-generate-desc') as HTMLButtonElement;
    const fileId = descContainer.getAttribute('data-id');

    const startEditing = () => {
      textSpan.classList.add('hidden');
      editBtn.closest('div')?.classList.add('hidden'); // Hide the button container
      inputEl.classList.remove('hidden');
      inputEl.focus();
      // Move cursor to end
      inputEl.selectionStart = inputEl.selectionEnd = inputEl.value.length;
    };

    const stopEditing = async (save: boolean) => {
      // Prevent double-saving if blur is triggered after Enter
      if (inputEl.classList.contains('hidden')) return; 

      inputEl.classList.add('hidden');
      textSpan.classList.remove('hidden');
      editBtn.closest('div')?.classList.remove('hidden');
      
      if (save && fileId) {
        const newDesc = inputEl.value.trim();
        const currentDesc = textSpan.getAttribute('data-desc') || '';
        
        if (newDesc !== currentDesc) {
          try {
            // Optimistic UI update
            textSpan.textContent = newDesc;
            if (!newDesc) textSpan.innerHTML = '<span class="italic opacity-50">Add description...</span>';
            textSpan.setAttribute('title', newDesc);
            textSpan.setAttribute('data-desc', newDesc);
            
            await api.updateFileDescription(fileId, newDesc);
            // Optionally sync store in background
            const updatedFiles = await api.listFiles();
            store.setUploadedFiles(updatedFiles);
          } catch (err) {
            console.error('Update description failed', err);
            // Revert UI on failure
            inputEl.value = currentDesc;
            textSpan.textContent = currentDesc;
            if (!currentDesc) textSpan.innerHTML = '<span class="italic opacity-50">Add description...</span>';
            textSpan.setAttribute('title', currentDesc);
            textSpan.setAttribute('data-desc', currentDesc);
            alert('Failed to update description.');
          }
        }
      } else {
        // Revert input value if cancelled
        inputEl.value = textSpan.getAttribute('data-desc') || '';
      }
    };

    generateBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!fileId) return;

      const originalContent = generateBtn.innerHTML;
      generateBtn.innerHTML = '<span class="material-symbols-outlined text-[16px] animate-spin">sync</span>';
      generateBtn.disabled = true;
      textSpan.classList.add('opacity-50');

      try {
        const result = await api.generateFileDescription(fileId);
        textSpan.textContent = result.description || '';
        textSpan.setAttribute('title', result.description || '');
        textSpan.setAttribute('data-desc', result.description || '');
        inputEl.value = result.description || '';
        
        // Sync store
        const updatedFiles = await api.listFiles();
        store.setUploadedFiles(updatedFiles);
      } catch (err: any) {
        console.error('Generation failed', err);
        const errorMsg = err.message || 'Unknown error';
        alert(`Failed to generate description: ${errorMsg}. Make sure Ollama is running and configured.`);
      } finally {
        generateBtn.innerHTML = originalContent;
        generateBtn.disabled = false;
        textSpan.classList.remove('opacity-50');
      }
    });

    textSpan.addEventListener('click', startEditing);
    editBtn.addEventListener('click', startEditing);
    
    inputEl.addEventListener('blur', () => stopEditing(true));
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        stopEditing(true);
      } else if (e.key === 'Escape') {
        stopEditing(false);
      }
    });
  });

  closeModal?.addEventListener('click', () => hideModal());
  modal.addEventListener('click', (e) => {
    if (e.target === modal) hideModal();
  });

  async function handleUpload(file: File) {
    const dropZoneContent = container.querySelector('#drop-zone-content');
    const dropZoneLoading = container.querySelector('#drop-zone-loading');
    
    // Show loading state
    if (dropZoneContent && dropZoneLoading) {
      dropZoneContent.classList.add('opacity-0');
      dropZoneLoading.classList.remove('opacity-0', 'pointer-events-none');
    }

    try {
      const result = await api.uploadFile(file);
      
      if (result.is_duplicate) {
        alert(`Duplicate Data Detected: "${file.name}" has already been uploaded and processed. We've skipped the duplicate effort for you!`);
      }

      const updatedFiles = await api.listFiles();
      store.setUploadedFiles(updatedFiles);
    } catch (err) {
      console.error('Upload failed', err);
      alert('Upload failed. Please check the console for details.');
    } finally {
      // Hide loading state
      if (dropZoneContent && dropZoneLoading) {
        dropZoneContent.classList.remove('opacity-0');
        dropZoneLoading.classList.add('opacity-0', 'pointer-events-none');
      }
    }
  }

  async function showPreview(tableName: string, filename: string) {
    modalTitle.textContent = filename;
    modal.classList.remove('hidden');
    setTimeout(() => {
      modal.classList.remove('opacity-0');
      modal.querySelector('div')?.classList.remove('translate-y-4');
    }, 10);

    try {
      const data = await api.getPreview(tableName);
      if (data.length === 0) {
        modalContent.innerHTML = '<div class="text-center text-neutral-500 py-20 italic">No data found in this table.</div>';
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
      modalContent.innerHTML = `<div class="text-center text-red-400 py-20">Failed to load preview: ${err}</div>`;
    }
  }

  function hideModal() {
    modal.classList.add('opacity-0');
    modal.querySelector('div')?.classList.add('translate-y-4');
    setTimeout(() => {
      modal.classList.add('hidden');
      modalContent.innerHTML = '<div class="flex items-center justify-center h-full"><span class="material-symbols-outlined animate-spin text-primary">sync</span></div>';
    }, 300);
  }

  return container;
}
