import './style.css';
import { createIcons, MessageSquare, LayoutDashboard, Database, Settings, Plus, Play } from 'lucide';
import { store } from './store';
import { api } from './services/api';
import { renderSidebar } from './components/Sidebar';
import { renderNotebook } from './components/Notebook';

const app = document.querySelector<HTMLDivElement>('#app')!;

function updateUI() {
  app.innerHTML = '';
  
  const shell = document.createElement('div');
  shell.className = 'flex w-full h-screen overflow-hidden';
  
  shell.appendChild(renderSidebar());
  shell.appendChild(renderNotebook());
  
  app.appendChild(shell);

  // Initialize Icons
  createIcons({
    icons: {
      MessageSquare,
      LayoutDashboard,
      Database,
      Settings,
      Plus,
      Play
    }
  });
}

// Initial Load
async function init() {
  try {
    const analyses = await api.listAnalyses();
    store.setAnalyses(analyses);
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
