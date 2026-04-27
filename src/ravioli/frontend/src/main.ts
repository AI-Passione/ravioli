import './style.css';
import { store } from './store';
import { api } from './services/api';
import { renderSidebar } from './components/Sidebar';
import { renderNotebook } from './components/Notebook';
import { renderInsights } from './components/Insights';
import { renderCreateAnalysis } from './components/CreateAnalysis';
import { renderKnowledge } from './components/Knowledge';
import { renderData } from './components/Data';
import { renderSettings } from './components/Settings';

const app = document.querySelector<HTMLDivElement>('#app')!;

function updateUI() {
  app.innerHTML = '';
  
  const shell = document.createElement('div');
  shell.className = 'flex w-full h-screen overflow-hidden relative';
  
  shell.appendChild(renderSidebar());
  
  const currentView = store.getCurrentView();
  const activeId = store.getActiveAnalysisId();
  if (currentView === 'create-analysis') {
    shell.appendChild(renderCreateAnalysis());
  } else if (currentView === 'knowledge') {
    shell.appendChild(renderKnowledge());
  } else if (currentView === 'data') {
    shell.appendChild(renderData());
  } else if (currentView === 'settings') {
    shell.appendChild(renderSettings());
  } else if (currentView === 'insights' && !activeId) {
    shell.appendChild(renderInsights());
  } else {
    shell.appendChild(renderNotebook());
  }
  
  app.appendChild(shell);
}

// Initial Load
async function init() {
  try {
    // Fetch analyses
    try {
      const analyses = await api.listAnalyses();
      console.log(`Fetched ${analyses.length} analyses from API`);
      store.setAnalyses(analyses);
    } catch (err) {
      console.error('Failed to fetch analyses', err);
    }

    // Fetch files
    try {
      const files = await api.listFiles();
      store.setUploadedFiles(files);
    } catch (err) {
      console.error('Failed to fetch files', err);
    }
  } catch (err) {
    console.error('Initialization failed', err);
  }
}

// --- Global ingestion progress poller ---
// Survives UI re-renders (unlike intervals defined inside renderData).
// Polls every 3s while any file is 'pending', updating the store directly.
let ingestionPollInterval: ReturnType<typeof setInterval> | null = null;

function startIngestionPollingIfNeeded() {
  const hasPending = store.getUploadedFiles().some(f => f.status === 'pending');
  if (hasPending && !ingestionPollInterval) {
    ingestionPollInterval = setInterval(async () => {
      try {
        const files = await api.listFiles();
        store.setUploadedFiles(files);
        // Stop polling once nothing is pending anymore
        if (!files.some(f => f.status === 'pending')) {
          clearInterval(ingestionPollInterval!);
          ingestionPollInterval = null;
        }
      } catch (err) {
        console.error('Ingestion poll failed', err);
      }
    }, 3000);
  }
}

// Polling for logs
let pollInterval: any;
store.subscribe(() => {
  const activeId = store.getActiveAnalysisId();
  
  // Clear previous interval
  if (pollInterval) clearInterval(pollInterval);
  
  if (activeId) {
    const fetchLogs = async () => {
      try {
        const logs = await api.listLogs(activeId);
        // Only update if logs changed to avoid unnecessary re-renders
        if (JSON.stringify(logs) !== JSON.stringify(store.getLogs())) {
          store.setLogs(logs);
        }
      } catch (err) {
        console.error('Failed to fetch logs', err);
      }
    };
    
    fetchLogs();
    pollInterval = setInterval(fetchLogs, 3000);
  }

  updateUI();

  // Kick off ingestion progress polling if any file is pending
  startIngestionPollingIfNeeded();
});

init();
updateUI();

