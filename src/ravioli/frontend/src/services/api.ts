import type { Analysis, AnalysisCreate, AnalysisLog, DataSource, QuickInsightResponse, WFSLayer, Insight, InsightStats, InsightsSummary, KnowledgePage, KnowledgePageCreate, KnowledgePageUpdate } from '../types';

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

  async approveAnalysis(id: string): Promise<Analysis> {
    const response = await fetch(`${API_BASE}/analyses/${id}/approve`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to approve analysis');
    return response.json();
  },

  async deleteAnalysis(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/analyses/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete analysis');
  },

  async listLogs(analysisId: string): Promise<AnalysisLog[]> {
    const response = await fetch(`${API_BASE}/analysis-logs/analysis/${analysisId}`);
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
  
  streamQuestion(analysisId: string, question: string, onMessage: (token: string) => void, onComplete: () => void, onError: (err: any) => void) {
    const url = `${API_BASE}/analyses/${analysisId}/stream?question=${encodeURIComponent(question)}`;
    const eventSource = new EventSource(url);
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        onComplete();
      } else {
        onMessage(event.data);
      }
    };
    
    eventSource.onerror = (err) => {
      eventSource.close();
      onError(err);
    };

    return () => eventSource.close();
  },
  
  async getSuggestedPrompts(analysisId: string): Promise<string[]> {
    const response = await fetch(`${API_BASE}/analyses/${analysisId}/suggested-prompts`);
    if (!response.ok) throw new Error('Failed to fetch suggested prompts');
    return response.json();
  },


  async generateQuickInsight(file: File): Promise<QuickInsightResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/analyses/quick-insight`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to generate quick insight');
    return response.json();
  },

  async generateQuickInsightFromExisting(fileId: string): Promise<QuickInsightResponse> {
    const response = await fetch(`${API_BASE}/analyses/quick-insight/existing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId }),
    });
    if (!response.ok) throw new Error('Failed to generate quick insight');
    return response.json();
  },

  async listFiles(): Promise<DataSource[]> {
    const response = await fetch(`${API_BASE}/data/files`);
    if (!response.ok) throw new Error('Failed to fetch files');
    return response.json();
  },

  async uploadFile(file: File): Promise<DataSource> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/data/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload file');
    return response.json();
  },

  streamUpload(file: File, onLog: (msg: string) => void, onComplete: (result: DataSource) => void, onError: (err: any) => void) {
    const formData = new FormData();
    formData.append('file', file);

    fetch(`${API_BASE}/data/upload-stream`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) throw new Error('Upload failed');
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) return;

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() || '';
        
        for (const chunk of chunks) {
          if (chunk.startsWith('data: ')) {
            const content = chunk.substring(6);
            if (content.startsWith('LOG:')) {
              onLog(content.substring(4));
            } else if (content.startsWith('DONE:')) {
              onComplete(JSON.parse(content.substring(5)));
            } else if (content.startsWith('ERROR:')) {
              onError(new Error(content.substring(6)));
            }
          }
        }
      }
    }).catch(onError);
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

  async updateFileDescription(fileId: string, description: string): Promise<DataSource> {
    const response = await fetch(`${API_BASE}/data/files/${fileId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    if (!response.ok) throw new Error('Failed to update file description');
    return response.json();
  },

  async togglePIITag(fileId: string, hasPII: boolean): Promise<DataSource> {
    const response = await fetch(`${API_BASE}/data/files/${fileId}/pii`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ has_pii: hasPII }),
    });
    if (!response.ok) throw new Error('Failed to update PII status');
    return response.json();
  },

  async generateFileDescription(fileId: string): Promise<DataSource> {
    const response = await fetch(`${API_BASE}/data/files/${fileId}/generate-description`, {
      method: 'POST',
    });
    if (!response.ok) {
      let detail: string;
      try {
        const errorData = await response.json();
        detail = errorData.detail || response.statusText;
      } catch (e) {
        detail = response.statusText;
      }
      throw new Error(detail);
    }
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
  },

  async testOllamaConnection(): Promise<{status: string, message: string, models?: string[]}> {
    const response = await fetch(`${API_BASE}/settings/ollama/test`);
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Connection test failed');
    }
    return response.json();
  },

  async getInsightStats(): Promise<InsightStats> {
    const response = await fetch(`${API_BASE}/insights/stats`);
    if (!response.ok) throw new Error('Failed to fetch insight stats');
    return response.json();
  },

  async getInsightsSummary(days: number): Promise<InsightsSummary> {
    const response = await fetch(`${API_BASE}/insights/summary?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch insights summary');
    return response.json();
  },

  async getReviewQueue(): Promise<Insight[]> {
    const response = await fetch(`${API_BASE}/insights/review-queue`);
    if (!response.ok) throw new Error('Failed to fetch review queue');
    return response.json();
  },

  async getInsightsFeed(days: number = 30): Promise<Insight[]> {
    const response = await fetch(`${API_BASE}/insights/feed?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch insights feed');
    return response.json();
  },

  async verifyInsight(id: string): Promise<Insight> {
    const response = await fetch(`${API_BASE}/insights/${id}/verify`, { method: 'PATCH' });
    if (!response.ok) throw new Error('Failed to verify insight');
    return response.json();
  },

  async rejectInsight(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/insights/${id}/reject`, { method: 'PATCH' });
    if (!response.ok) throw new Error('Failed to reject insight');
  },

  async getWFSLayers(url: string): Promise<WFSLayer[]> {
    const response = await fetch(`${API_BASE}/data/wfs/layers?url=${encodeURIComponent(url)}`);
    if (!response.ok) throw new Error('Failed to fetch WFS layers');
    return response.json();
  },

  async ingestWFSLayer(url: string, layer?: string): Promise<DataSource> {
    const response = await fetch(`${API_BASE}/data/wfs/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, ...(layer ? { layer } : {}) }),
    });
    if (!response.ok) throw new Error('Failed to ingest WFS layer');
    return response.json();
  },
  
  async listKnowledgePages(): Promise<KnowledgePage[]> {
    const response = await fetch(`${API_BASE}/knowledge/`);
    if (!response.ok) throw new Error('Failed to fetch knowledge pages');
    return response.json();
  },

  async getKnowledgePage(id: string): Promise<KnowledgePage> {
    const response = await fetch(`${API_BASE}/knowledge/${id}`);
    if (!response.ok) throw new Error('Failed to fetch knowledge page');
    return response.json();
  },

  async createKnowledgePage(data: KnowledgePageCreate): Promise<KnowledgePage> {
    const response = await fetch(`${API_BASE}/knowledge/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create knowledge page');
    return response.json();
  },

  async updateKnowledgePage(id: string, data: KnowledgePageUpdate): Promise<KnowledgePage> {
    const response = await fetch(`${API_BASE}/knowledge/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update knowledge page');
    return response.json();
  },

  async deleteKnowledgePage(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/knowledge/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete knowledge page');
  }
};
