// Job-related types
export interface Job {
  id: number;
  job_id?: string;
  company: string;
  job_title: string;
  job_description: string;
  job_url?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  source: string;
  status: string;
  job_type?: string;
  match_score?: number;
  recommendation?: 'apply_now' | 'apply_with_confidence' | 'consider_carefully' | 'not_recommended' | 'skip';
  created_at: string;
  updated_at: string;
  application_deadline?: string;
  notes?: string;
  strengths?: string[];
  concerns?: string[];
  missing_skills?: string[];
}

export interface JobCreate {
  company: string;
  job_title: string;
  job_description: string;
  job_url?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  source: string;
}

export interface JobFilters {
  status_filter?: string;
  min_score?: number;
  source?: string;
  skip?: number;
  limit?: number;
  location?: string;
  job_type?: string;
  company?: string;
  search?: string;
}

export interface JobAnalysis {
  job_id: number;
  match_score: number;
  recommendation: string;
  strengths: string[];
  concerns: string[];
  analysis_details: {
    semantic_similarity: number;
    skill_match: number;
    location_match: number;
    salary_match: number;
  };
  created_at: string;
}
