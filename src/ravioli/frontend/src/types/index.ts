export interface Analysis {
  id: string;
  title: string;
  description?: string;
  status: string;
  analysis_metadata?: any;
  created_at: string;
  updated_at: string;
}

export interface ExecutionLog {
  id: string;
  analysis_id: string;
  log_type: string;
  content: string;
  tool_name?: string;
  data?: any;
  timestamp: string;
}

export interface AnalysisCreate {
  title: string;
  description?: string;
  analysis_metadata?: any;
}

export interface UploadedFile {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  table_name: string;
  row_count?: number;
  status: string;
  error_message?: string;
  file_hash?: string;
  is_duplicate?: boolean;
  created_at: string;
  updated_at: string;
}

export interface SystemSetting {
  key: string;
  value: Record<string, any>;
  updated_at?: string;
}

export interface QuickInsightResponse {
  analysis_id: string;
  title: string;
  summary: string;
  stats: Record<string, number>;
  followup_questions: string[];
}
