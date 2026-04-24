import './style.css';
import { store } from './store';
import { api } from './services/api';
import { renderSidebar } from './components/Sidebar';
import { renderNotebook } from './components/Notebook';
import { renderCreateAnalysis } from './components/CreateAnalysis';
import { renderKnowledge } from './components/Knowledge';
import { renderData } from './components/Data';

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
  } else {
    shell.appendChild(renderNotebook());
  }
  
  app.appendChild(shell);
}

// Initial Load
async function init() {
  try {
    const [analyses, files] = await Promise.all([
      api.listAnalyses(),
      api.listFiles()
    ]);
    
    store.setAnalyses(analyses);
    store.setUploadedFiles(files);
    
    if (analyses.length > 0) {
      store.setActiveAnalysisId(analyses[0].id);
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
  
  updateUI();
});

init();
updateUI();
