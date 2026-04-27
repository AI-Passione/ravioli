import './style.css';
import { store } from './store';
import { api } from './services/api';
import { renderSidebar } from './components/Sidebar';
import { renderNotebook } from './components/Notebook';
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
  if (currentView === 'create-analysis') {
    shell.appendChild(renderCreateAnalysis());
  } else if (currentView === 'knowledge') {
    shell.appendChild(renderKnowledge());
  } else if (currentView === 'data') {
    shell.appendChild(renderData());
  } else if (currentView === 'settings') {
    shell.appendChild(renderSettings());
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
      if (analyses.length > 0 && !store.getActiveAnalysisId()) {
        // Removed auto-selecting the first analysis to default to the Dashboard tab
      }
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

  // Refresh files if we are in data view
  if (store.getCurrentView() === 'data') {
    // Files are already up-to-date in the store (refreshFiles() in Data.ts
    // fetches and commits before calling store.setUploadedFiles). Just re-render.
  }
  
  updateUI();
});

init();
updateUI();
