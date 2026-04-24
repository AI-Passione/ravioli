import { store } from '../store';
import { api } from '../services/api';

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
                    <code class="px-2 py-1 rounded bg-surface-container-highest text-primary-fixed-dim text-xs font-mono">${file.table_name}</code>
                  </td>
                  <td class="px-8 py-5 text-neutral-300 font-medium">
                    ${file.row_count ? file.row_count.toLocaleString() : '--'}
                  </td>
                  <td class="px-8 py-5 text-neutral-400 text-sm">
                    ${(file.size_bytes / 1024).toFixed(1)} KB
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
