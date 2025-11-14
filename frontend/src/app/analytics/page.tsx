'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import SuccessPatterns from '@/components/analytics/SuccessPatterns';
import StatsCard from '@/components/dashboard/StatsCard';
import { LoadingPage } from '@/components/common/LoadingSpinner';
import { useAnalyticsOverview, useSuccessPatterns } from '@/hooks/useAnalytics';

export default function AnalyticsPage() {
  const { data: overview, isLoading: overviewLoading } = useAnalyticsOverview();
  const { data: patterns, isLoading: patternsLoading } = useSuccessPatterns();

  if (overviewLoading || patternsLoading) {
    return <LoadingPage text="Loading analytics..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-2 text-gray-600">
          Track your progress and gain insights into your job search
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Success Rate"
          value={`${overview?.success_rate || 0}%`}
          color="green"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatsCard
          title="Response Rate"
          value={`${overview?.response_rate || 0}%`}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
        />
        <StatsCard
          title="Avg. Time to Offer"
          value={`${overview?.avg_days_to_offer || 0}d`}
          color="purple"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatsCard
          title="Active Applications"
          value={overview?.active_applications || 0}
          color="yellow"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
      </div>

      {/* Application Funnel */}
      <Card>
        <CardHeader>
          <CardTitle>Application Funnel</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { stage: 'Saved', count: overview?.funnel?.saved || 0, color: 'bg-gray-500' },
              { stage: 'Applied', count: overview?.funnel?.applied || 0, color: 'bg-blue-500' },
              { stage: 'Screening', count: overview?.funnel?.screening || 0, color: 'bg-indigo-500' },
              { stage: 'Interviewing', count: overview?.funnel?.interviewing || 0, color: 'bg-purple-500' },
              { stage: 'Offer', count: overview?.funnel?.offer || 0, color: 'bg-green-500' },
            ].map((stage, index) => {
              const percentage = overview?.funnel?.saved
                ? ((stage.count / overview.funnel.saved) * 100).toFixed(1)
                : 0;

              return (
                <div key={stage.stage}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">{stage.stage}</span>
                    <span className="text-sm text-gray-600">
                      {stage.count} ({percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`${stage.color} h-3 rounded-full transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Success Patterns */}
      <SuccessPatterns patterns={patterns || []} />

      {/* Recent Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-gray-500">
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
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p className="mt-2">Trend charts coming soon</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
