import type { Mission, ExecutionLog } from './types';

type Listener = () => void;

class Store {
  private missions: Mission[] = [];
  private activeMissionId?: string;
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

  setMissions(missions: Mission[]) {
    this.missions = missions;
    this.notify();
  }

  getMissions() { return this.missions; }

  setActiveMissionId(id?: string) {
    this.activeMissionId = id;
    this.notify();
  }

  getActiveMissionId() { return this.activeMissionId; }

  setLogs(logs: ExecutionLog[]) {
    this.logs = logs;
    this.notify();
  }

  getLogs() { return this.logs; }
}

export const store = new Store();
