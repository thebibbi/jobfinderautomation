import React from 'react';
import Badge from '@/components/common/Badge';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const statusConfig: Record<string, { variant: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple', text: string }> = {
    saved: { variant: 'default', text: 'Saved' },
    applied: { variant: 'info', text: 'Applied' },
    screening: { variant: 'info', text: 'Screening' },
    interviewing: { variant: 'purple', text: 'Interviewing' },
    technical_assessment: { variant: 'purple', text: 'Assessment' },
    offer_received: { variant: 'success', text: 'Offer Received' },
    accepted: { variant: 'success', text: 'Accepted' },
    rejected: { variant: 'danger', text: 'Rejected' },
    withdrawn: { variant: 'warning', text: 'Withdrawn' },
    archived: { variant: 'default', text: 'Archived' },
  };

  const config = statusConfig[status] || { variant: 'default' as const, text: status };

  return (
    <Badge variant={config.variant} size={size} dot>
      {config.text}
    </Badge>
  );
}
