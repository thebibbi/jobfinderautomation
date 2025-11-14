import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Merge Tailwind classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format currency
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Format date
export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

// Format relative time
export function formatRelativeTime(date: string): string {
  const now = new Date();
  const then = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (diffInSeconds < 60) return 'just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;

  return formatDate(date);
}

// Get status color
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    saved: 'blue',
    applied: 'yellow',
    interviewing: 'purple',
    offer_received: 'green',
    accepted: 'green',
    rejected: 'red',
    withdrawn: 'gray',
  };
  return colors[status] || 'gray';
}

// Get match score color
export function getMatchScoreColor(score: number): string {
  if (score >= 90) return 'green';
  if (score >= 80) return 'blue';
  if (score >= 70) return 'yellow';
  if (score >= 50) return 'orange';
  return 'red';
}

// Get recommendation badge
export function getRecommendationBadge(recommendation: string): {
  text: string;
  color: string;
  emoji: string;
} {
  const badges: Record<string, { text: string; color: string; emoji: string }> = {
    apply_now: { text: 'Apply Now', color: 'green', emoji: '🎯' },
    apply_with_confidence: { text: 'Apply', color: 'blue', emoji: '✨' },
    consider_carefully: { text: 'Consider', color: 'yellow', emoji: '🤔' },
    not_recommended: { text: 'Skip', color: 'red', emoji: '⚠️' },
  };
  return badges[recommendation] || { text: recommendation, color: 'gray', emoji: '📊' };
}

// Truncate text
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
}

// Calculate days between dates
export function daysBetween(date1: string, date2: string): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// Format salary range
export function formatSalaryRange(min?: number, max?: number): string {
  if (!min && !max) return 'Not specified';
  if (min && max) return `${formatCurrency(min)} - ${formatCurrency(max)}`;
  if (min) return `${formatCurrency(min)}+`;
  if (max) return `Up to ${formatCurrency(max)}`;
  return 'Not specified';
}
