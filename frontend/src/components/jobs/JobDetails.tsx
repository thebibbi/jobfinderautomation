'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Button from '@/components/common/Button';
import { Job } from '@/types/job';
import { formatDate, formatCurrency, getMatchScoreColor } from '@/lib/utils';

interface JobDetailsProps {
  job: Job;
  onApply?: () => void;
  onUpdateStatus?: (status: string) => void;
}

export default function JobDetails({ job, onApply, onUpdateStatus }: JobDetailsProps) {
  const matchScoreColor = job.match_score ? getMatchScoreColor(job.match_score) : 'gray';

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{job.job_title}</h1>
            <p className="text-xl text-gray-600 mt-2">{job.company}</p>
          </div>

          {/* Quick Info */}
          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            {job.location && (
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                <span>{job.location}</span>
              </div>
            )}
            {job.job_type && (
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{job.job_type}</span>
              </div>
            )}
            {job.salary_min && job.salary_max && (
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{formatCurrency(job.salary_min)} - {formatCurrency(job.salary_max)}</span>
              </div>
            )}
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-2">
            {job.source && <Badge variant="default">{job.source}</Badge>}
            {job.status && <Badge variant="info">{job.status}</Badge>}
            {job.recommendation && <Badge variant="success">{job.recommendation}</Badge>}
          </div>

          {/* Match Score */}
          {job.match_score !== undefined && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Match Score</span>
                <span className={`text-2xl font-bold text-${matchScoreColor}-600`}>
                  {job.match_score}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`bg-${matchScoreColor}-600 h-2 rounded-full transition-all`}
                  style={{ width: `${job.match_score}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            {job.status === 'saved' && (
              <Button variant="primary" onClick={onApply}>
                Apply Now
              </Button>
            )}
            <Button variant="secondary" onClick={() => window.open(job.job_url, '_blank')}>
              View Original
            </Button>
            {onUpdateStatus && (
              <Button variant="ghost" onClick={() => onUpdateStatus('archived')}>
                Archive
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Job Description */}
      <Card>
        <CardHeader>
          <CardTitle>Job Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
            {job.job_description}
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {(job.strengths || job.concerns || job.missing_skills) && (
        <Card>
          <CardHeader>
            <CardTitle>AI Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {job.strengths && job.strengths.length > 0 && (
                <div>
                  <h4 className="font-semibold text-green-700 mb-2">Strengths</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {job.strengths.map((strength, index) => (
                      <li key={index} className="text-sm text-gray-700">{strength}</li>
                    ))}
                  </ul>
                </div>
              )}

              {job.concerns && job.concerns.length > 0 && (
                <div>
                  <h4 className="font-semibold text-yellow-700 mb-2">Concerns</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {job.concerns.map((concern, index) => (
                      <li key={index} className="text-sm text-gray-700">{concern}</li>
                    ))}
                  </ul>
                </div>
              )}

              {job.missing_skills && job.missing_skills.length > 0 && (
                <div>
                  <h4 className="font-semibold text-red-700 mb-2">Missing Skills</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {job.missing_skills.map((skill, index) => (
                      <li key={index} className="text-sm text-gray-700">{skill}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="font-medium text-gray-500">Added</dt>
              <dd className="mt-1 text-gray-900">{formatDate(job.created_at)}</dd>
            </div>
            {job.updated_at && (
              <div>
                <dt className="font-medium text-gray-500">Last Updated</dt>
                <dd className="mt-1 text-gray-900">{formatDate(job.updated_at)}</dd>
              </div>
            )}
            {job.application_deadline && (
              <div>
                <dt className="font-medium text-gray-500">Application Deadline</dt>
                <dd className="mt-1 text-gray-900">{formatDate(job.application_deadline)}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
