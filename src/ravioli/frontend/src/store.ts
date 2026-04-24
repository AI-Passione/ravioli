import type { Analysis, ExecutionLog, UploadedFile } from './types';

type Listener = () => void;

class Store {
  private analyses: Analysis[] = [];
  private activeAnalysisId?: string;
  private logs: ExecutionLog[] = [];
  private uploadedFiles: UploadedFile[] = [];
  private currentView: 'dashboard' | 'create-analysis' | 'knowledge' | 'warehouse' = 'dashboard';
  private listeners: Listener[] = [];

  subscribe(listener: Listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(l => l());
  }

  setAnalyses(analyses: Analysis[]) {
    this.analyses = analyses;
    this.notify();
  }

  getAnalyses() { return this.analyses; }

  setActiveAnalysisId(id?: string) {
    this.activeAnalysisId = id;
    this.currentView = 'dashboard';
    this.notify();
  }

  getActiveAnalysisId() { return this.activeAnalysisId; }

  setCurrentView(view: 'dashboard' | 'create-analysis' | 'knowledge' | 'warehouse') {
    this.currentView = view;
    if (view === 'create-analysis' || view === 'warehouse' || view === 'knowledge') {
      this.activeAnalysisId = undefined;
    }
    this.notify();
  }

  getCurrentView() { return this.currentView; }

  setLogs(logs: ExecutionLog[]) {
    this.logs = logs;
    this.notify();
  }

  getLogs() { return this.logs; }

  setUploadedFiles(files: UploadedFile[]) {
    this.uploadedFiles = files;
    this.notify();
  }

  getUploadedFiles() { return this.uploadedFiles; }
}

export const store = new Store();
