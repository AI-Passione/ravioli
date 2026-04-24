import { api } from '../services/api';

export function renderSettings() {
  const container = document.createElement('div');
  container.className = 'flex-1 bg-surface-container-lowest flex flex-col min-h-screen overflow-y-auto text-on-surface';

  let ollamaConfig = {
    base_url: 'http://localhost:11434',
    default_model: 'gemma3:4b',
    api_key: ''
  };

  const renderContent = () => {
    container.innerHTML = `
      <header class="px-12 pt-12 pb-8 max-w-4xl mx-auto w-full">
        <div class="flex items-center gap-3 mb-2">
          <div class="w-10 h-10 rounded-xl bg-surface-container-highest flex items-center justify-center border border-outline-variant/30">
            <span class="material-symbols-outlined text-primary-fixed-dim">settings</span>
          </div>
          <div>
            <h1 class="text-3xl font-display-lg tracking-tight text-neutral-100">Settings</h1>
            <p class="text-sm font-label-md text-on-surface-variant opacity-80 uppercase tracking-widest mt-1">Platform Integrations & Configuration</p>
          </div>
        </div>
      </header>

      <main class="flex-1 px-12 pb-12 max-w-4xl mx-auto w-full flex flex-col gap-8">
        
        <!-- AI Integrations -->
        <section>
          <h2 class="text-lg font-bold text-neutral-100 border-b border-outline-variant pb-2 mb-4">AI Models</h2>
          
          <div class="bg-surface-container-low border border-outline-variant/50 rounded-2xl overflow-hidden">
            <div class="p-6">
              <div class="flex items-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary-fixed-dim text-2xl">memory</span>
                <h3 class="text-xl font-medium text-neutral-100">Ollama</h3>
              </div>
              <p class="text-sm text-on-surface-variant mb-6">Configure your local or remote Ollama instance for AI model integration.</p>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Base URL</label>
                  <input id="ollama-base-url" type="text" value="${ollamaConfig.base_url}" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="e.g. http://localhost:11434" />
                </div>
                
                <div>
                  <label class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Default Model</label>
                  <input id="ollama-default-model" type="text" value="${ollamaConfig.default_model}" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="e.g. gemma3:4b" />
                </div>
                
                <div>
                  <label class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">API Key (Optional)</label>
                  <input id="ollama-api-key" type="password" value="${ollamaConfig.api_key}" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="Required for Ollama Cloud (e.g. sk-...)" />
                </div>
                
                <div class="pt-2 flex items-center gap-4">
                  <button id="btn-save-ai" class="bg-primary-fixed-dim text-on-primary-fixed font-bold py-2 px-6 rounded-full text-sm hover:brightness-110 transition-all shadow-md">
                    Save AI Settings
                  </button>
                  <span id="save-status" class="text-sm text-green-400 opacity-0 transition-opacity duration-300 font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">check_circle</span> Saved
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Gemini -->
          <div class="bg-surface-container-low border border-outline-variant/50 rounded-2xl overflow-hidden mt-4 relative group">
            <div class="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            <div class="p-6">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <span class="material-symbols-outlined text-purple-500 text-2xl">auto_awesome</span>
                  <h3 class="text-xl font-medium text-neutral-100">Google Gemini</h3>
                </div>
                <span class="text-[10px] bg-purple-500/20 text-purple-500 border border-purple-500/30 px-2 py-1 rounded-full font-bold uppercase tracking-wider">Coming Soon</span>
              </div>
              <p class="text-sm text-on-surface-variant mb-4">Integrate with Google's most capable AI models.</p>
              <button class="text-sm font-bold text-outline-variant cursor-not-allowed" disabled>Configure</button>
            </div>
          </div>
        </section>

        <!-- Data Warehouse Integrations -->
        <section>
          <h2 class="text-lg font-bold text-neutral-100 border-b border-outline-variant pb-2 mb-4">Data Warehouses</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <!-- Motherduck -->
            <div class="bg-surface-container-low border border-outline-variant/50 rounded-2xl p-6 relative group overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <span class="material-symbols-outlined text-yellow-500 text-2xl">database</span>
                  <h3 class="text-lg font-medium text-neutral-100">Motherduck</h3>
                </div>
                <span class="text-[10px] bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 px-2 py-1 rounded-full font-bold uppercase tracking-wider">Coming Soon</span>
              </div>
              <p class="text-sm text-on-surface-variant mb-4">Serverless cloud analytics using DuckDB.</p>
              <button class="text-sm font-bold text-outline-variant cursor-not-allowed" disabled>Configure</button>
            </div>

            <!-- BigQuery -->
            <div class="bg-surface-container-low border border-outline-variant/50 rounded-2xl p-6 relative group overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <span class="material-symbols-outlined text-blue-500 text-2xl">cloud</span>
                  <h3 class="text-lg font-medium text-neutral-100">BigQuery</h3>
                </div>
                <span class="text-[10px] bg-blue-500/20 text-blue-500 border border-blue-500/30 px-2 py-1 rounded-full font-bold uppercase tracking-wider">Coming Soon</span>
              </div>
              <p class="text-sm text-on-surface-variant mb-4">Google's fully managed, serverless data warehouse.</p>
              <button class="text-sm font-bold text-outline-variant cursor-not-allowed" disabled>Configure</button>
            </div>

            <!-- Snowflake -->
            <div class="bg-surface-container-low border border-outline-variant/50 rounded-2xl p-6 relative group overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <span class="material-symbols-outlined text-cyan-500 text-2xl">ac_unit</span>
                  <h3 class="text-lg font-medium text-neutral-100">Snowflake</h3>
                </div>
                <span class="text-[10px] bg-cyan-500/20 text-cyan-500 border border-cyan-500/30 px-2 py-1 rounded-full font-bold uppercase tracking-wider">Coming Soon</span>
              </div>
              <p class="text-sm text-on-surface-variant mb-4">Cloud computing-based data cloud company.</p>
              <button class="text-sm font-bold text-outline-variant cursor-not-allowed" disabled>Configure</button>
            </div>

          </div>
        </section>

      </main>
    `;

    container.querySelector('#btn-save-ai')?.addEventListener('click', async () => {
      const baseUrl = (container.querySelector('#ollama-base-url') as HTMLInputElement).value;
      const defaultModel = (container.querySelector('#ollama-default-model') as HTMLInputElement).value;
      const apiKey = (container.querySelector('#ollama-api-key') as HTMLInputElement).value;
      
      const btn = container.querySelector('#btn-save-ai') as HTMLButtonElement;
      btn.disabled = true;
      btn.classList.add('opacity-50');

      try {
        await api.updateSetting('ollama', {
          base_url: baseUrl,
          default_model: defaultModel,
          api_key: apiKey
        });
        
        const status = container.querySelector('#save-status');
        if (status) {
          status.classList.remove('opacity-0');
          setTimeout(() => status.classList.add('opacity-0'), 2000);
        }
      } catch (e) {
        console.error('Failed to save settings', e);
        // Could show error message here
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-50');
      }
    });
  };

  renderContent();

  // Load actual data
  api.getSetting('ollama').then(setting => {
    if (setting && setting.value && Object.keys(setting.value).length > 0) {
      ollamaConfig = { ...ollamaConfig, ...setting.value };
      renderContent();
    }
  }).catch(e => console.error('Failed to fetch settings', e));

  return container;
}
