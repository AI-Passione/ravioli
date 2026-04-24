import type { Analysis, AnalysisCreate, ExecutionLog } from '../types';

const API_BASE = '/api/v1';

export const api = {
  async listAnalyses(): Promise<Analysis[]> {
    const response = await fetch(`${API_BASE}/analyses/`);
    if (!response.ok) throw new Error('Failed to fetch analyses');
    return response.json();
  },

  async createAnalysis(data: AnalysisCreate): Promise<Analysis> {
    const response = await fetch(`${API_BASE}/analyses/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create analysis');
    return response.json();
  },

  async deleteAnalysis(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/analyses/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete analysis');
  },

  async listLogs(analysisId: string): Promise<ExecutionLog[]> {
    const response = await fetch(`${API_BASE}/logs/analysis/${analysisId}`);
    if (!response.ok) throw new Error('Failed to fetch logs');
    return response.json();
  },

  async askQuestion(analysisId: string, question: string): Promise<void> {
    const response = await fetch(`${API_BASE}/analyses/${analysisId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) throw new Error('Failed to ask question');
  }

  async generateQuickInsight(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/analyses/quick-insight`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to generate quick insight');
    return response.json();
  }
};
