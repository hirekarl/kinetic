// TypeScript interfaces mirroring the Python Pydantic output models in
// src/kinetic/models/outputs.py — single source of truth is the Python side.

export type StatusLevel = 'green' | 'yellow' | 'red';
export type AgentDomain = 'bio' | 'logistics' | 'relational' | 'system';

export interface TriageItem {
  id: string;
  priority: number; // 1-10, higher = more urgent
  domain: AgentDomain;
  description: string;
  action: string;
  snooze_until: string | null; // ISO 8601 datetime
  completed: boolean;
}

export interface ROISummary {
  time_recovered_minutes: number;
  margin_recovered: string;
  burnout_risk_delta: number;
}

export interface BioStatus {
  status: StatusLevel;
  burnout_score: number;
  forecast: string;
  sleep_debt_hours: number;
  recommendations: string[];
  error_message?: string;
}

export interface LogisticsStatus {
  status: StatusLevel;
  critical_tasks: string[];
  outsourcing_suggestions: string[];
  time_to_resolve_minutes: number;
  error_message?: string;
}

export interface RelationalStatus {
  status: StatusLevel;
  connection_margin_score: number;
  at_risk_relationships: string[];
  interaction_sprints: string[];
  error_message?: string;
}

export interface SystemHealthPayload {
  overall_status: StatusLevel;
  bio: BioStatus | null;
  logistics: LogisticsStatus | null;
  relational: RelationalStatus | null;
  triage_items: TriageItem[];
  roi_summary: ROISummary | null;
}

export interface CheckInRequest {
  message: string;
}
