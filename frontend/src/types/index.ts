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

export interface LogisticsTask {
  name: string;
  status: 'pending' | 'completed';
  days_overdue: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  subtasks: string[];
  completed_subtasks: string[];
  notes: string | null;
}

export interface LogisticsStatus {
  status: StatusLevel;
  critical_tasks: string[];
  tasks_with_steps: LogisticsTask[];
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

export interface BioTrend {
  avg_sleep_hours: number;
  sleep_slope: number; // negative = declining, positive = improving
  avg_nutrition: number;
  avg_energy: number;
  worst_sleep_day: string | null; // ISO date "YYYY-MM-DD"
  days_analyzed: number;
  sleep_series: number[]; // per-day hours oldest→newest
}

export interface RecurringTask {
  name: string;
  times_overdue: number;
  avg_days_overdue: number;
  priority: string;
}

export interface RelationalDrift {
  person: string;
  contact_trend: number; // avg daily increase in days_since_contact
  avg_vibe_score: number;
  last_known_days_since_contact: number;
}

export interface BehavioralSummary {
  bio_trend: BioTrend | null;
  recurring_tasks: RecurringTask[];
  relational_drifts: RelationalDrift[];
  days_analyzed: number;
  generated_at: string; // ISO 8601 datetime
}

export interface BehavioralProfile {
  profile_key: string;
  insight: string;
  evidence: Record<string, unknown>;
  first_observed: string; // ISO 8601 datetime
  last_updated: string; // ISO 8601 datetime
  observation_count: number;
}

export interface ContactPause {
  person: string;
  paused_until: string; // ISO date "YYYY-MM-DD"
  reason: string | null;
}

export interface SystemHealthPayload {
  overall_status: StatusLevel;
  bio: BioStatus | null;
  logistics: LogisticsStatus | null;
  relational: RelationalStatus | null;
  triage_items: TriageItem[];
  roi_summary: ROISummary | null;
  liaison_feedback: string | null;
  responding_agent: string | null;
  behavioral_profiles: BehavioralProfile[];
  behavioral_summary: BehavioralSummary | null;
  active_pauses: ContactPause[];
}

export interface CheckInRequest {
  message: string;
}
