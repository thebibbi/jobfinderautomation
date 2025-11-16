'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Button from '@/components/common/Button';
import { useLearnClick, useLearnDismiss } from '@/hooks/useRecommendations';
import { Recommendation } from '@/types/recommendation';
import { formatCurrency, formatRelativeTime } from '@/lib/utils';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const router = useRouter();
  const learnClick = useLearnClick();
  const learnDismiss = useLearnDismiss();
  const [dismissReason, setDismissReason] = useState('');
  const [showDismissInput, setShowDismissInput] = useState(false);

  const handleView = () => {
    learnClick.mutate(recommendation.job_id);
    router.push(`/jobs/${recommendation.job_id}`);
  };

  const handleDismiss = async () => {
    if (dismissReason.trim()) {
      await learnDismiss.mutateAsync({
        jobId: recommendation.job_id,
        reason: dismissReason,
      });
      setShowDismissInput(false);
      setDismissReason('');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-100';
    if (score >= 80) return 'text-blue-600 bg-blue-100';
    if (score >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <Card hoverable>
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
              {recommendation.job_title}
            </h3>
            <p className="text-sm text-gray-600 mt-1">{recommendation.company}</p>
          </div>
          <div className={`px-3 py-1 rounded-lg text-lg font-bold ${getScoreColor(recommendation.match_score || 0)}`}>
            {recommendation.match_score || 0}%
          </div>
        </div>

        {/* Match Reasons */}
        {recommendation.match_reasons && recommendation.match_reasons.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-700 mb-2">Why this matches:</p>
            <div className="flex flex-wrap gap-2">
              {recommendation.match_reasons.slice(0, 3).map((reason, index) => (
                <Badge key={index} variant="info" size="sm">
                  {reason}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Job Details */}
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          {recommendation.location && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              </svg>
              <span>{recommendation.location}</span>
            </div>
          )}
          {recommendation.salary_min && recommendation.salary_max && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>
                {formatCurrency(recommendation.salary_min)} - {formatCurrency(recommendation.salary_max)}
              </span>
            </div>
          )}
        </div>

        {/* Confidence Score */}
        <div className="bg-gray-50 rounded p-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Confidence Score</span>
            <span className="font-medium text-gray-900">
              {((recommendation.confidence_score || 0) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-blue-600 h-1.5 rounded-full"
              style={{ width: `${(recommendation.confidence_score || 0) * 100}%` }}
            />
          </div>
        </div>

        {/* Dismiss Input */}
        {showDismissInput && (
          <div className="bg-gray-50 rounded p-3 space-y-2">
            <input
              type="text"
              placeholder="Why are you dismissing this? (helps us learn)"
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              autoFocus
            />
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setShowDismissInput(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="danger"
                onClick={handleDismiss}
                disabled={!dismissReason.trim()}
                isLoading={learnDismiss.isPending}
              >
                Confirm Dismiss
              </Button>
            </div>
          </div>
        )}

        {/* Actions */}
        {!showDismissInput && (
          <div className="flex gap-2 pt-3 border-t border-gray-200">
            <Button variant="primary" fullWidth onClick={handleView}>
              View Details
            </Button>
            <Button
              variant="ghost"
              onClick={() => setShowDismissInput(true)}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          </div>
        )}

        {/* Footer */}
        <div className="text-xs text-gray-500">
          Recommended {formatRelativeTime(recommendation.recommended_at || new Date().toISOString())}
        </div>
      </div>
    </Card>
  );
}
