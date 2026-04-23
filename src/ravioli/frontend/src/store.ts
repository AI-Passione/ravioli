import type { Analysis, ExecutionLog } from './types';

type Listener = () => void;

class Store {
  private analyses: Analysis[] = [];
  private activeAnalysisId?: string;
  private logs: ExecutionLog[] = [];
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
    this.notify();
  }

  getActiveAnalysisId() { return this.activeAnalysisId; }

  setLogs(logs: ExecutionLog[]) {
    this.logs = logs;
    this.notify();
  }

  getLogs() { return this.logs; }
}

export const store = new Store();
