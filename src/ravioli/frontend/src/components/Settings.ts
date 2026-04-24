import { api } from '../services/api';

export function renderSettings() {
  const container = document.createElement('div');
  container.className = 'flex-1 bg-surface-container-lowest flex flex-col min-h-screen overflow-y-auto text-on-surface';

  let ollamaConfig = {
    mode: 'default', // 'default', 'local', 'cloud'
    base_url: 'http://localhost:11434',
    default_model: 'gemma3:4b',
    api_key: ''
  };
  // True when the backend already has an encrypted key stored
  let apiKeyIsSet = false;
  
  let isConfiguringOllama = false;

  const renderContent = () => {
    
    // Build Ollama content based on state
    let ollamaContent = '';
    
    if (!isConfiguringOllama) {
      ollamaContent = `
        <div class="pt-2">
          <button id="btn-configure-ollama" class="bg-surface-container-highest border border-outline-variant/50 text-neutral-100 font-bold py-2 px-6 rounded-full text-sm hover:bg-surface-container transition-all shadow-sm">
            Configure
          </button>
        </div>
      `;
    } else {
      ollamaContent = `
        <div class="space-y-6 mt-4">
          <div class="space-y-3">
            <label class="flex items-center gap-3 p-3 rounded-lg border ${ollamaConfig.mode === 'default' ? 'border-primary-fixed-dim bg-primary-fixed-dim/10' : 'border-outline-variant/50 bg-surface-container-highest'} cursor-pointer transition-colors">
              <input type="radio" name="ollama-mode" value="default" class="text-primary-fixed-dim focus:ring-primary-fixed-dim" ${ollamaConfig.mode === 'default' ? 'checked' : ''}>
              <div class="flex flex-col">
                <span class="text-sm font-bold text-neutral-100">Default</span>
                <span class="text-xs text-on-surface-variant">Use the built-in default model of Gemma3:4b from local Ollama</span>
              </div>
            </label>
            
            <label class="flex items-center gap-3 p-3 rounded-lg border ${ollamaConfig.mode === 'local' ? 'border-primary-fixed-dim bg-primary-fixed-dim/10' : 'border-outline-variant/50 bg-surface-container-highest'} cursor-pointer transition-colors">
              <input type="radio" name="ollama-mode" value="local" class="text-primary-fixed-dim focus:ring-primary-fixed-dim" ${ollamaConfig.mode === 'local' ? 'checked' : ''}>
              <div class="flex flex-col">
                <span class="text-sm font-bold text-neutral-100">Custom Local Runtime</span>
                <span class="text-xs text-on-surface-variant">Enter a custom base URL to another Ollama server on your network</span>
              </div>
            </label>
            
            <label class="flex items-center gap-3 p-3 rounded-lg border ${ollamaConfig.mode === 'cloud' ? 'border-primary-fixed-dim bg-primary-fixed-dim/10' : 'border-outline-variant/50 bg-surface-container-highest'} cursor-pointer transition-colors">
              <input type="radio" name="ollama-mode" value="cloud" class="text-primary-fixed-dim focus:ring-primary-fixed-dim" ${ollamaConfig.mode === 'cloud' ? 'checked' : ''}>
              <div class="flex flex-col">
                <span class="text-sm font-bold text-neutral-100">Ollama Cloud</span>
                <span class="text-xs text-on-surface-variant">Connect to Ollama Cloud with an API Key</span>
              </div>
            </label>
          </div>
          
          <div class="space-y-4 pt-2 border-t border-outline-variant/30">
            ${ollamaConfig.mode === 'local' ? `
              <div>
                <label class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Base URL</label>
                <input id="ollama-base-url" type="text" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="e.g. http://localhost:11434" />
              </div>
            ` : ''}
            
            ${ollamaConfig.mode !== 'default' ? `
              <div>
                <label class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">Default Model</label>
                <input id="ollama-default-model" type="text" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="e.g. gemma3:4b" />
              </div>
            ` : ''}
            
            ${ollamaConfig.mode === 'cloud' ? `
              <div>
                <label class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider mb-2">API Key</label>
                ${apiKeyIsSet ? `
                  <div class="flex items-center gap-3 mb-2">
                    <span class="flex items-center gap-1 text-xs font-bold text-green-400 bg-green-400/10 border border-green-400/30 px-3 py-1 rounded-full">
                      <span class="material-symbols-outlined text-sm">lock</span> Key stored securely
                    </span>
                    <button id="btn-clear-key" class="text-xs text-on-surface-variant hover:text-red-400 transition-colors underline">Replace key</button>
                  </div>
                  <input id="ollama-api-key" type="password" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="Enter new API key to replace the stored one" />
                ` : `
                  <input id="ollama-api-key" type="password" class="w-full bg-surface-container-highest border border-outline-variant/50 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim transition-colors" placeholder="Required for Ollama Cloud (e.g. sk-...)" />
                `}
              </div>
            ` : ''}
            
            <div class="pt-2 flex items-center gap-4">
              <button id="btn-save-ai" class="bg-primary-fixed-dim text-on-primary-fixed font-bold py-2 px-6 rounded-full text-sm hover:brightness-110 transition-all shadow-md">
                Save AI Settings
              </button>
              <button id="btn-test-ollama" class="bg-surface-container-highest border border-outline-variant/50 text-neutral-100 font-bold py-2 px-6 rounded-full text-sm hover:bg-surface-container transition-all shadow-sm flex items-center gap-2">
                <span class="material-symbols-outlined text-sm">network_check</span> Test Connection
              </button>
              <button id="btn-cancel-ollama" class="text-sm font-bold text-on-surface-variant hover:text-neutral-100 transition-colors">
                Cancel
              </button>
              <span id="save-status" class="text-sm text-green-400 opacity-0 transition-opacity duration-300 font-bold flex items-center gap-1 ml-auto">
                <span class="material-symbols-outlined text-sm">check_circle</span> Saved
              </span>
            </div>
            <div id="test-status" class="text-xs mt-2 hidden p-3 rounded-lg border"></div>
          </div>
        </div>
      `;
    }

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
              <p class="text-sm text-on-surface-variant mb-2">Configure your local or remote Ollama instance for AI model integration.</p>
              
              ${ollamaContent}
              
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

    // ── Safely populate input values via DOM (prevents XSS from innerHTML interpolation) ──
    const baseUrlInput = container.querySelector('#ollama-base-url') as HTMLInputElement | null;
    if (baseUrlInput) baseUrlInput.value = ollamaConfig.base_url;

    const defaultModelInput = container.querySelector('#ollama-default-model') as HTMLInputElement | null;
    if (defaultModelInput) defaultModelInput.value = ollamaConfig.default_model;

    // Attach listeners
    const configureBtn = container.querySelector('#btn-configure-ollama');
    if (configureBtn) {
      configureBtn.addEventListener('click', () => {
        isConfiguringOllama = true;
        renderContent();
      });
    }

    const cancelBtn = container.querySelector('#btn-cancel-ollama');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        isConfiguringOllama = false;
        renderContent();
      });
    }

    const modeRadios = container.querySelectorAll('input[name="ollama-mode"]');
    modeRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        ollamaConfig.mode = (e.target as HTMLInputElement).value;
        renderContent(); // re-render to show/hide fields
      });
    });

    const testBtn = container.querySelector('#btn-test-ollama');
    if (testBtn) {
      testBtn.addEventListener('click', async () => {
        const btn = testBtn as HTMLButtonElement;
        const statusDiv = container.querySelector('#test-status') as HTMLDivElement;
        const originalText = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span> Testing...';
        statusDiv.classList.remove('hidden', 'bg-green-400/10', 'border-green-400/30', 'text-green-400', 'bg-red-400/10', 'border-red-400/30', 'text-red-400');
        statusDiv.classList.add('bg-surface-container-highest', 'border-outline-variant/30', 'text-on-surface-variant');
        statusDiv.textContent = 'Contacting server...';
        statusDiv.classList.remove('hidden');

        try {
          // First save the current values so the test uses what's in the inputs
          const urlInput = container.querySelector('#ollama-base-url') as HTMLInputElement;
          if (urlInput) ollamaConfig.base_url = urlInput.value;
          const modelInput = container.querySelector('#ollama-default-model') as HTMLInputElement;
          if (modelInput) ollamaConfig.default_model = modelInput.value;
          const keyInput = container.querySelector('#ollama-api-key') as HTMLInputElement;
          if (keyInput && keyInput.value) ollamaConfig.api_key = keyInput.value;

          await api.updateSetting('ollama', {
            mode: ollamaConfig.mode,
            base_url: ollamaConfig.base_url,
            default_model: ollamaConfig.default_model,
            api_key: ollamaConfig.api_key === '••••••••' ? '••••••••' : ollamaConfig.api_key
          });

          const result = await api.testOllamaConnection();
          statusDiv.classList.remove('bg-surface-container-highest', 'border-outline-variant/30', 'text-on-surface-variant');
          statusDiv.classList.add('bg-green-400/10', 'border-green-400/30', 'text-green-400');
          statusDiv.innerHTML = `<div class="flex items-center gap-2"><span class="material-symbols-outlined text-sm">check_circle</span> ${result.message}</div>`;
          if (result.models && result.models.length > 0) {
            statusDiv.innerHTML += `<div class="mt-1 opacity-80">Available models: ${result.models.join(', ')}</div>`;
          }
        } catch (e: any) {
          statusDiv.classList.remove('bg-surface-container-highest', 'border-outline-variant/30', 'text-on-surface-variant');
          statusDiv.classList.add('bg-red-400/10', 'border-red-400/30', 'text-red-400');
          statusDiv.innerHTML = `<div class="flex items-center gap-2"><span class="material-symbols-outlined text-sm">error</span> ${e.message}</div>`;
        } finally {
          btn.disabled = false;
          btn.innerHTML = originalText;
        }
      });
    }

    const saveBtn = container.querySelector('#btn-save-ai');
    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        // Collect current values from inputs if they exist
        const urlInput = container.querySelector('#ollama-base-url') as HTMLInputElement;
        if (urlInput) ollamaConfig.base_url = urlInput.value;
        
        const modelInput = container.querySelector('#ollama-default-model') as HTMLInputElement;
        if (modelInput) ollamaConfig.default_model = modelInput.value;
        
        const REDACTED = '••••••••';
        const keyInput = container.querySelector('#ollama-api-key') as HTMLInputElement;
        if (keyInput && keyInput.value && keyInput.value !== REDACTED) {
          // User typed a new key — send it for encryption
          ollamaConfig.api_key = keyInput.value;
        } else if (apiKeyIsSet) {
          // No new value — signal backend to keep the existing encrypted value
          ollamaConfig.api_key = REDACTED;
        } else {
          ollamaConfig.api_key = '';
        }
        
        // If mode is default, force the values back to defaults just in case
        if (ollamaConfig.mode === 'default') {
          ollamaConfig.base_url = 'http://localhost:11434';
          ollamaConfig.default_model = 'gemma3:4b';
          ollamaConfig.api_key = '';
        }

        const btn = saveBtn as HTMLButtonElement;
        btn.disabled = true;
        btn.classList.add('opacity-50');

        try {
          await api.updateSetting('ollama', {
            mode: ollamaConfig.mode,
            base_url: ollamaConfig.base_url,
            default_model: ollamaConfig.default_model,
            api_key: ollamaConfig.api_key
          });
          
          const status = container.querySelector('#save-status');
          if (status) {
            status.classList.remove('opacity-0');
            setTimeout(() => {
              status.classList.add('opacity-0');
              setTimeout(() => {
                isConfiguringOllama = false;
                renderContent();
              }, 300);
            }, 1500);
          }
        } catch (e) {
          console.error('Failed to save settings', e);
        } finally {
          btn.disabled = false;
          btn.classList.remove('opacity-50');
        }
      });
    }
  };

  renderContent();

  // Load actual data
  api.getSetting('ollama').then(setting => {
    if (setting && setting.value && Object.keys(setting.value).length > 0) {
      const { api_key, ...rest } = setting.value;
      // The backend returns '••••••••' when a key is stored — track that separately
      apiKeyIsSet = api_key === '••••••••';
      ollamaConfig = { ...ollamaConfig, ...rest, api_key: '' };
      renderContent();
    }
  }).catch(e => console.error('Failed to fetch settings', e));

  return container;
}
