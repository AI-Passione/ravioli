export interface Analysis {
  id: string;
  title: string;
  description?: string;
  status: string;
  result?: string;
  analysis_metadata?: {
    type?: string;
    filename?: string;
    row_count?: number;
    followup_questions?: string[];
    is_approved?: boolean;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface AnalysisLog {
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

export interface DataSource {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  table_name: string;
  schema_name: string;
  row_count?: number;
  status: string;
  error_message?: string;
  file_hash?: string;
  is_duplicate?: boolean;
  source_type?: string;
  source_url?: string;
  has_pii: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface WFSLayer {
  name: string;
  title: string;
  formats: string[];
}

export interface SystemSetting {
  key: string;
  value: Record<string, any>;
  updated_at?: string;
}

export interface Insight {
  id: string;
  analysis_id: string;
  content: string;
  source_label?: string;
  assumptions?: string;
  limitations?: string;
  metadata?: {
    basic_stats?: string;
    appendix?: string;
    [key: string]: any;
  };
  is_verified: boolean;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface InsightStats {
  verified_count: number;
  analyses_count: number;
  contributors_count: number;
}

export interface InsightsSummary {
  summary: string;
  insight_count: number;
  days: number;
}

export interface QuickInsightResponse {
  analysis_id: string;
  title: string;
  summary: string;
  stats: Record<string, number>;
  followup_questions: string[];
}
