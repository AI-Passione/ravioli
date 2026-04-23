import type { Mission, MissionCreate, ExecutionLog } from '../types';

const API_BASE = '/api/v1';

export const api = {
  async listMissions(): Promise<Mission[]> {
    const response = await fetch(`${API_BASE}/missions/`);
    if (!response.ok) throw new Error('Failed to fetch missions');
    return response.json();
  },

  async createMission(data: MissionCreate): Promise<Mission> {
    const response = await fetch(`${API_BASE}/missions/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create mission');
    return response.json();
  },

  async getMission(id: string): Promise<Mission> {
    const response = await fetch(`${API_BASE}/missions/${id}`);
    if (!response.ok) throw new Error('Failed to fetch mission');
    return response.json();
  },

  async deleteMission(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/missions/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete mission');
  },

  async listLogs(missionId: string): Promise<ExecutionLog[]> {
    const response = await fetch(`${API_BASE}/logs/?mission_id=${missionId}`);
    if (!response.ok) throw new Error('Failed to fetch logs');
    return response.json();
  },

  async askQuestion(missionId: string, question: string): Promise<void> {
    const response = await fetch(`${API_BASE}/missions/${missionId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) throw new Error('Failed to ask question');
  }
};
