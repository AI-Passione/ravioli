import type { Analysis, AnalysisCreate, ExecutionLog, UploadedFile } from '../types';

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
  },

  async generateQuickInsight(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/analyses/quick-insight`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to generate quick insight');
    return response.json();
  },

  async listFiles(): Promise<UploadedFile[]> {
    const response = await fetch(`${API_BASE}/data/files`);
    if (!response.ok) throw new Error('Failed to fetch files');
    return response.json();
  },

  async uploadFile(file: File): Promise<UploadedFile> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/data/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload file');
    return response.json();
  },

  async getPreview(tableName: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/data/preview/${tableName}`);
    if (!response.ok) throw new Error('Failed to fetch preview');
    return response.json();
  },

  async deleteFile(fileId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/data/files/${fileId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete file');
  },

  async updateFileDescription(fileId: string, description: string): Promise<UploadedFile> {
    const response = await fetch(`${API_BASE}/data/files/${fileId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    if (!response.ok) throw new Error('Failed to update file description');
    return response.json();
  },

  async generateFileDescription(fileId: string): Promise<UploadedFile> {
    const response = await fetch(`${API_BASE}/data/files/${fileId}/generate-description`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to generate file description');
    return response.json();
  },

  async getSetting(key: string): Promise<any> {
    const response = await fetch(`${API_BASE}/settings/${key}`);
    if (response.status === 404) return { key, value: {} };
    if (!response.ok) throw new Error('Failed to fetch setting');
    return response.json();
  },

  async updateSetting(key: string, value: Record<string, any>): Promise<any> {
    const response = await fetch(`${API_BASE}/settings/${key}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value }),
    });
    if (!response.ok) throw new Error('Failed to update setting');
    return response.json();
  }
};
