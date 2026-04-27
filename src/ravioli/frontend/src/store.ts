import type { Analysis, AnalysisLog, DataSource } from './types';

type Listener = () => void;

class Store {
  private analyses: Analysis[] = [];
  private activeAnalysisId?: string;
  private logs: AnalysisLog[] = [];
  private dataSources: DataSource[] = [];
  private currentView: 'insights' | 'dashboard' | 'create-analysis' | 'knowledge' | 'data' | 'settings' | 'governance' = 'insights';
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
    if (id) {
      this.currentView = 'dashboard';
    }
    this.notify();
  }

  refreshAnalysis(updated: import('./types').Analysis) {
    this.analyses = this.analyses.map(a => a.id === updated.id ? updated : a);
    this.notify();
  }

  getActiveAnalysisId() { return this.activeAnalysisId; }

  setCurrentView(view: 'insights' | 'dashboard' | 'create-analysis' | 'knowledge' | 'data' | 'settings' | 'governance') {
    this.currentView = view;
    if (view === 'insights' || view === 'create-analysis' || view === 'data' || view === 'knowledge' || view === 'settings' || view === 'governance') {
      this.activeAnalysisId = undefined;
    }
    this.notify();
  }

  getCurrentView() { return this.currentView; }

  setLogs(logs: AnalysisLog[]) {
    this.logs = logs;
    this.notify();
  }

  getLogs() { return this.logs; }

  setDataSources(sources: DataSource[]) {
    this.dataSources = sources;
    this.notify();
  }

  getDataSources() { return this.dataSources; }
}

export const store = new Store();
