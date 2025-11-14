'use client';

import React, { useState } from 'react';
import RecommendationCard from '@/components/recommendations/RecommendationCard';
import Select from '@/components/common/Select';
import { LoadingPage } from '@/components/common/LoadingSpinner';
import { useRecommendations } from '@/hooks/useRecommendations';
import { RecommendationFilters } from '@/types/recommendation';

export default function RecommendationsPage() {
  const [filters, setFilters] = useState<RecommendationFilters>({
    min_score: 70,
  });
  const { data: recommendations, isLoading, error } = useRecommendations(filters);

  if (isLoading) {
    return <LoadingPage text="Loading recommendations..." />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load recommendations. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Recommended Jobs</h1>
        <p className="mt-2 text-gray-600">
          AI-powered job recommendations based on your profile and preferences
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Select
            label="Minimum Match Score"
            value={filters.min_score?.toString() || '70'}
            onChange={(e) => setFilters({ ...filters, min_score: parseInt(e.target.value) })}
            options={[
              { value: '50', label: '50% or higher' },
              { value: '60', label: '60% or higher' },
              { value: '70', label: '70% or higher' },
              { value: '80', label: '80% or higher' },
              { value: '90', label: '90% or higher' },
            ]}
          />
          <Select
            label="Location"
            value={filters.location || ''}
            onChange={(e) => setFilters({ ...filters, location: e.target.value || undefined })}
            options={[
              { value: '', label: 'All Locations' },
              { value: 'remote', label: 'Remote' },
              { value: 'san-francisco', label: 'San Francisco' },
              { value: 'new-york', label: 'New York' },
              { value: 'seattle', label: 'Seattle' },
            ]}
          />
          <Select
            label="Job Type"
            value={filters.job_type || ''}
            onChange={(e) => setFilters({ ...filters, job_type: e.target.value || undefined })}
            options={[
              { value: '', label: 'All Types' },
              { value: 'full-time', label: 'Full-time' },
              { value: 'part-time', label: 'Part-time' },
              { value: 'contract', label: 'Contract' },
            ]}
          />
        </div>
      </div>

      {/* Recommendations Grid */}
      {recommendations && recommendations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((rec) => (
            <RecommendationCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No recommendations yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Add more jobs and apply to build your profile for better recommendations.
          </p>
        </div>
      )}
    </div>
  );
}
