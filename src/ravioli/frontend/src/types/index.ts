export interface Mission {
  id: string;
  title: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ExecutionLog {
  id: string;
  mission_id: string;
  log_type: string;
  content: string;
  tool_name?: string;
  data?: any;
  timestamp: string;
}

export interface MissionCreate {
  title: string;
  description?: string;
  mission_metadata?: any;
}
