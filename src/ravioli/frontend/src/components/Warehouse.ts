import { store } from '../store';
import { api } from '../services/api';

export function renderWarehouse() {
  const container = document.createElement('main');
  container.className = 'flex-1 h-full overflow-hidden bg-surface flex flex-col p-8 pt-12';

  const files = store.getUploadedFiles();

  container.innerHTML = `
    <div class="max-w-6xl mx-auto w-full">
      <header class="mb-12">
        <h1 class="text-4xl font-medium tracking-tight text-neutral-100 mb-2">Warehouse</h1>
        <p class="text-neutral-500 max-w-2xl">Manage your data assets. Ingest CSV files into DuckDB for high-performance analytics.</p>
      </header>

      <!-- Upload Zone -->
      <div class="mb-12">
        <div id="drop-zone" class="border-2 border-dashed border-outline/30 rounded-3xl p-12 flex flex-col items-center justify-center bg-surface-container-low hover:bg-surface-container hover:border-primary/50 transition-all cursor-pointer group">
          <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <span class="material-symbols-outlined text-primary text-3xl">upload_file</span>
          </div>
          <h3 class="text-xl font-medium text-neutral-200 mb-2">Drop your CSV here</h3>
          <p class="text-neutral-500 text-sm">or click to browse your files</p>
          <input type="file" id="file-input" class="hidden" accept=".csv">
        </div>
      </div>

      <!-- Files List -->
      <div class="bg-surface-container-low rounded-3xl overflow-hidden border border-outline/10">
        <div class="px-8 py-6 border-b border-outline/10 flex items-center justify-between">
          <h2 class="text-lg font-medium text-neutral-200">Ingested Assets</h2>
          <span class="text-xs text-neutral-500 uppercase tracking-widest">${files.length} Files</span>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead>
              <tr class="text-[10px] uppercase tracking-[0.2em] text-neutral-500 border-b border-outline/5">
                <th class="px-8 py-4 font-medium">Asset Name</th>
                <th class="px-8 py-4 font-medium">DuckDB Table</th>
                <th class="px-8 py-4 font-medium">Size</th>
                <th class="px-8 py-4 font-medium">Status</th>
                <th class="px-8 py-4 font-medium text-right">Added</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline/5">
              ${files.length === 0 ? `
                <tr>
                  <td colspan="5" class="px-8 py-12 text-center text-neutral-500 italic">No assets ingested yet.</td>
                </tr>
              ` : files.map(file => `
                <tr class="hover:bg-white/5 transition-colors group">
                  <td class="px-8 py-5">
                    <div class="flex items-center gap-3">
                      <span class="material-symbols-outlined text-neutral-400 group-hover:text-primary transition-colors">description</span>
                      <span class="text-neutral-200 font-medium">${file.original_filename}</span>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    <code class="px-2 py-1 rounded bg-surface-container-highest text-primary-fixed-dim text-xs">${file.table_name}</code>
                  </td>
                  <td class="px-8 py-5 text-neutral-400 text-sm">
                    ${(file.size_bytes / 1024).toFixed(1)} KB
                  </td>
                  <td class="px-8 py-5">
                    <span class="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-bold ${
                      file.status === 'completed' ? 'bg-green-500/10 text-green-400' : 
                      file.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                    }">
                      ${file.status}
                    </span>
                  </td>
                  <td class="px-8 py-5 text-right text-neutral-500 text-sm">
                    ${new Date(file.created_at).toLocaleDateString()}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  // Event Listeners
  const dropZone = container.querySelector('#drop-zone');
  const fileInput = container.querySelector('#file-input') as HTMLInputElement;

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

  async function handleUpload(file: File) {
    try {
      // Show loading or optimistic update? For now just call API
      await api.uploadFile(file);
      // Refresh list
      const updatedFiles = await api.listFiles();
      store.setUploadedFiles(updatedFiles);
    } catch (err) {
      console.error('Upload failed', err);
      alert('Upload failed. Please check the console for details.');
    }
  }

  return container;
}
