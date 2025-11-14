'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { Job } from '@/types/job';
import { formatRelativeTime, getMatchScoreColor, formatCurrency } from '@/lib/utils';

interface JobCardProps {
  job: Job;
}

export default function JobCard({ job }: JobCardProps) {
  const router = useRouter();

  const getRecommendationBadge = () => {
    if (!job.recommendation) return null;

    const variants = {
      apply_now: { variant: 'success' as const, text: 'Apply Now' },
      apply_with_confidence: { variant: 'info' as const, text: 'Good Match' },
      consider_carefully: { variant: 'warning' as const, text: 'Consider' },
      skip: { variant: 'danger' as const, text: 'Skip' },
    };

    const badge = variants[job.recommendation];
    return badge ? <Badge variant={badge.variant} size="sm">{badge.text}</Badge> : null;
  };

  const getStatusBadge = () => {
    const variants = {
      saved: { variant: 'default' as const, text: 'Saved' },
      applied: { variant: 'info' as const, text: 'Applied' },
      interviewing: { variant: 'purple' as const, text: 'Interviewing' },
      offer_received: { variant: 'success' as const, text: 'Offer' },
      rejected: { variant: 'danger' as const, text: 'Rejected' },
      archived: { variant: 'default' as const, text: 'Archived' },
    };

    const badge = variants[job.status as keyof typeof variants];
    return badge ? <Badge variant={badge.variant} size="sm" dot>{badge.text}</Badge> : null;
  };

  const matchScoreColor = job.match_score ? getMatchScoreColor(job.match_score) : 'gray';
  const colorClasses = {
    green: 'text-green-600 bg-green-100',
    blue: 'text-blue-600 bg-blue-100',
    yellow: 'text-yellow-600 bg-yellow-100',
    red: 'text-red-600 bg-red-100',
    gray: 'text-gray-600 bg-gray-100',
  };

  return (
    <Card
      hoverable
      onClick={() => router.push(`/jobs/${job.id}`)}
      className="cursor-pointer"
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
              {job.job_title}
            </h3>
            <p className="text-sm text-gray-600 mt-1">{job.company}</p>
          </div>
          {getStatusBadge()}
        </div>

        {/* Match Score & Recommendation */}
        <div className="flex items-center gap-3">
          {job.match_score !== undefined && (
            <div className="flex items-center gap-2">
              <div className={`px-2 py-1 rounded text-sm font-semibold ${colorClasses[matchScoreColor]}`}>
                {job.match_score}%
              </div>
              <span className="text-xs text-gray-500">Match</span>
            </div>
          )}
          {getRecommendationBadge()}
        </div>

        {/* Location & Salary */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          {job.location && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="line-clamp-1">{job.location}</span>
            </div>
          )}
          {job.salary_min && job.salary_max && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{formatCurrency(job.salary_min)} - {formatCurrency(job.salary_max)}</span>
            </div>
          )}
        </div>

        {/* Description Preview */}
        {job.job_description && (
          <p className="text-sm text-gray-600 line-clamp-2">
            {job.job_description}
          </p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200">
          <div className="flex items-center gap-2">
            {job.source && (
              <Badge variant="default" size="sm">
                {job.source}
              </Badge>
            )}
            {job.job_type && (
              <Badge variant="info" size="sm">
                {job.job_type}
              </Badge>
            )}
          </div>
          <span className="text-xs text-gray-500">
            {formatRelativeTime(job.created_at)}
          </span>
        </div>
      </div>
    </Card>
  );
}
