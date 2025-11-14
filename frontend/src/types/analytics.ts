// Analytics-related types
export interface AnalyticsOverview {
  period: string;
  summary: {
    total_jobs_tracked: number;
    total_applications: number;
    active_applications: number;
    interviews_scheduled: number;
    offers_received: number;
    offers_accepted: number;
  };
  conversion_funnel: {
    jobs_saved: number;
    jobs_applied: number;
    applications_to_interview: number;
    interviews_to_offer: number;
    offers_to_acceptance: number;
  };
  conversion_rates: {
    save_to_apply: number;
    apply_to_interview: number;
    interview_to_offer: number;
    offer_to_accept: number;
    overall_success_rate: number;
  };
  timeline_metrics: {
    average_days_to_apply: number;
    average_days_to_interview: number;
    average_days_to_offer: number;
    average_application_lifetime: number;
  };
}

export interface FunnelAnalysis {
  period: {
    start: string;
    end: string;
  };
  overall_funnel: {
    stage_1_saved: number;
    stage_2_applied: number;
    stage_3_interviewing: number;
    stage_4_offer: number;
    stage_5_accepted: number;
  };
  breakdown_by_source?: Record<string, any>;
  drop_off_analysis: {
    highest_drop_off: string;
    drop_off_rate: number;
    reasons: string[];
  };
}

export interface TrendData {
  metric: string;
  granularity: string;
  data_points: TrendDataPoint[];
  trend: 'increasing' | 'decreasing' | 'stable';
  average: number;
  peak: {
    period: string;
    value: number;
  };
}

export interface TrendDataPoint {
  period: string;
  start_date: string;
  end_date: string;
  value: number;
  change_from_previous?: string;
}

export interface SuccessPatterns {
  successful_applications: number;
  common_patterns: {
    match_score_range: {
      min: number;
      avg: number;
      max: number;
    };
    company_characteristics: {
      size: string[];
      industries: string[];
      locations: string[];
    };
    skills_frequently_matched: string[];
    timeline_patterns: {
      avg_days_to_apply: number;
      avg_days_to_interview: number;
      avg_days_to_offer: number;
    };
  };
  recommendations: string[];
}
