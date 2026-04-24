export interface Analysis {
  id: string;
  title: string;
  description?: string;
  status: string;
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
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
