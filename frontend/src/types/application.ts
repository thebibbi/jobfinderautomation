// Application-related types
import { Job } from './job';

export interface Application extends Job {
  // Inherits from Job
}

export interface StatusUpdate {
  status: string;
  notes?: string;
}

export interface ApplicationTimeline {
  job_id: number;
  events: TimelineEvent[];
  interviews: Interview[];
  offers: Offer[];
  notes: Note[];
}

export interface TimelineEvent {
  id: number;
  event_type: string;
  from_status?: string;
  to_status?: string;
  notes?: string;
  created_at: string;
}

export interface Interview {
  id: number;
  job_id: number;
  interview_type: 'phone' | 'video' | 'onsite' | 'technical' | 'behavioral' | 'panel';
  scheduled_date: string;
  duration_minutes?: number;
  location?: string;
  interviewer_name?: string;
  interviewer_email?: string;
  preparation_notes?: string;
  outcome?: 'passed' | 'rejected' | 'pending' | 'cancelled';
  feedback?: string;
  calendar_event_id?: string;
  created_at: string;
}

export interface Offer {
  id: number;
  job_id: number;
  base_salary: number;
  bonus?: number;
  equity?: string;
  other_benefits?: string;
  offer_status: 'pending' | 'negotiating' | 'accepted' | 'declined' | 'expired';
  received_date: string;
  expiration_date?: string;
  decision_date?: string;
  negotiation_history?: any[];
  notes?: string;
  created_at: string;
}

export interface Note {
  id: number;
  job_id: number;
  note_type: 'general' | 'communication' | 'preparation' | 'research' | 'follow_up';
  content: string;
  is_important: boolean;
  created_at: string;
  updated_at: string;
}

export interface ATSStatistics {
  total_applications: number;
  by_status: Record<string, number>;
  interview_stats: {
    total_interviews: number;
    upcoming: number;
    completed: number;
    passed: number;
    rejected: number;
  };
  offer_stats: {
    total_offers: number;
    pending: number;
    accepted: number;
    declined: number;
    average_base_salary?: number;
  };
  success_rate: number;
  average_days_to_offer?: number;
}
