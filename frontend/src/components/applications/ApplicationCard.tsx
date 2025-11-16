'use client';

import React from 'react';
import { useDrag } from 'react-dnd';
import { Card } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { formatRelativeTime, getStatusColor } from '@/lib/utils';

interface Application {
  id: number;
  job_title: string;
  company: string;
  status: string;
  applied_date?: string;
  last_updated: string;
  match_score?: number;
  next_step?: string;
}

interface ApplicationCardProps {
  application: Application;
  onClick?: () => void;
}

export default function ApplicationCard({ application, onClick }: ApplicationCardProps) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'APPLICATION',
    item: { id: application.id, status: application.status },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  return (
    <div
      ref={drag as any}
      style={{ opacity: isDragging ? 0.5 : 1 }}
      className="cursor-move"
    >
      <Card hoverable onClick={onClick} padding="sm">
        <div className="space-y-2">
          {/* Header */}
          <div>
            <h4 className="font-semibold text-gray-900 text-sm line-clamp-1">
              {application.job_title}
            </h4>
            <p className="text-xs text-gray-600 mt-0.5">{application.company}</p>
          </div>

          {/* Match Score */}
          {application.match_score !== undefined && (
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full"
                  style={{ width: `${application.match_score}%` }}
                />
              </div>
              <span className="text-xs font-medium text-gray-700">
                {application.match_score}%
              </span>
            </div>
          )}

          {/* Next Step */}
          {application.next_step && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
              <p className="text-xs text-yellow-800">
                <span className="font-medium">Next:</span> {application.next_step}
              </p>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{formatRelativeTime(application.last_updated)}</span>
            {application.applied_date && (
              <span>Applied {formatRelativeTime(application.applied_date)}</span>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
