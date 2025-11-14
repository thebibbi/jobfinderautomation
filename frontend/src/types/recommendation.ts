// Recommendation-related types
export interface Recommendation {
  job_id: number;
  company: string;
  job_title: string;
  location?: string;
  recommendation_score: number;
  match_score?: number;
  reasons: string[];
  preference_factors: {
    skills_match: number;
    location_match: number;
    salary_match: number;
    company_size_match: number;
    behavioral_score: number;
  };
}

export interface RecommendationFilters {
  limit?: number;
  algorithm?: 'content' | 'collaborative' | 'hybrid';
  include_reasons?: boolean;
  filter_applied?: boolean;
  min_score?: number;
}

export interface RecommendationResponse {
  recommendations: Recommendation[];
  algorithm_used: string;
  generated_at: string;
}
