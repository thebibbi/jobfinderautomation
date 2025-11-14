'use client';

import React from 'react';
import { Card } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Button from '@/components/common/Button';
import { formatDate, formatRelativeTime } from '@/lib/utils';

interface Interview {
  id: number;
  job_id: number;
  job_title: string;
  company: string;
  interview_type: string;
  scheduled_date: string;
  duration_minutes?: number;
  location?: string;
  interviewer_name?: string;
  notes?: string;
  status: string;
}

interface InterviewCardProps {
  interview: Interview;
  onEdit?: () => void;
  onCancel?: () => void;
}

export default function InterviewCard({ interview, onEdit, onCancel }: InterviewCardProps) {
  const isUpcoming = new Date(interview.scheduled_date) > new Date();
  const isPast = new Date(interview.scheduled_date) < new Date();

  const getTypeColor = (type: string) => {
    const colors: Record<string, 'info' | 'purple' | 'success' | 'warning'> = {
      phone_screen: 'info',
      technical: 'purple',
      behavioral: 'success',
      final: 'warning',
    };
    return colors[type] || 'default';
  };

  const getStatusBadge = () => {
    if (interview.status === 'completed') {
      return <Badge variant="success" size="sm">Completed</Badge>;
    }
    if (interview.status === 'cancelled') {
      return <Badge variant="danger" size="sm">Cancelled</Badge>;
    }
    if (isPast) {
      return <Badge variant="warning" size="sm">Pending Update</Badge>;
    }
    return <Badge variant="info" size="sm" dot>Upcoming</Badge>;
  };

  return (
    <Card hoverable>
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{interview.job_title}</h3>
            <p className="text-sm text-gray-600 mt-1">{interview.company}</p>
          </div>
          {getStatusBadge()}
        </div>

        {/* Interview Type */}
        <div>
          <Badge variant={getTypeColor(interview.interview_type)}>
            {interview.interview_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </Badge>
        </div>

        {/* Date & Time */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <div>
              <p className="font-medium text-blue-900">{formatDate(interview.scheduled_date)}</p>
              <p className="text-sm text-blue-700">
                {isUpcoming && `In ${formatRelativeTime(interview.scheduled_date)}`}
                {isPast && `Was ${formatRelativeTime(interview.scheduled_date)}`}
              </p>
            </div>
          </div>
          {interview.duration_minutes && (
            <p className="text-sm text-blue-700 mt-2">
              Duration: {interview.duration_minutes} minutes
            </p>
          )}
        </div>

        {/* Details */}
        <div className="space-y-2 text-sm">
          {interview.location && (
            <div className="flex items-center gap-2 text-gray-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              </svg>
              <span>{interview.location}</span>
            </div>
          )}
          {interview.interviewer_name && (
            <div className="flex items-center gap-2 text-gray-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span>{interview.interviewer_name}</span>
            </div>
          )}
        </div>

        {/* Notes */}
        {interview.notes && (
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs font-medium text-gray-700 mb-1">Notes:</p>
            <p className="text-sm text-gray-600">{interview.notes}</p>
          </div>
        )}

        {/* Actions */}
        {isUpcoming && interview.status !== 'cancelled' && (
          <div className="flex gap-2 pt-3 border-t border-gray-200">
            {onEdit && (
              <Button variant="secondary" size="sm" onClick={onEdit}>
                Edit
              </Button>
            )}
            <Button variant="primary" size="sm" fullWidth>
              Join Meeting
            </Button>
            {onCancel && (
              <Button variant="danger" size="sm" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
