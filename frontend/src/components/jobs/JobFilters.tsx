'use client';

import React, { useState } from 'react';
import { Card } from '@/components/common/Card';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Button from '@/components/common/Button';
import { JobFilters as JobFiltersType } from '@/types/job';

interface JobFiltersProps {
  filters: JobFiltersType;
  onFiltersChange: (filters: JobFiltersType) => void;
}

export default function JobFilters({ filters, onFiltersChange }: JobFiltersProps) {
  const [localFilters, setLocalFilters] = useState<JobFiltersType>(filters);

  const handleFilterChange = (key: keyof JobFiltersType, value: any) => {
    setLocalFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    onFiltersChange(localFilters);
  };

  const resetFilters = () => {
    const emptyFilters: JobFiltersType = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  return (
    <Card>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>

        {/* Status Filter */}
        <Select
          label="Status"
          value={localFilters.status_filter || ''}
          onChange={(e) => handleFilterChange('status_filter', e.target.value || undefined)}
          options={[
            { value: '', label: 'All Statuses' },
            { value: 'saved', label: 'Saved' },
            { value: 'applied', label: 'Applied' },
            { value: 'interviewing', label: 'Interviewing' },
            { value: 'offer_received', label: 'Offer Received' },
            { value: 'rejected', label: 'Rejected' },
            { value: 'archived', label: 'Archived' },
          ]}
        />

        {/* Match Score Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Match Score
          </label>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={localFilters.min_score || 0}
            onChange={(e) => handleFilterChange('min_score', parseInt(e.target.value) || undefined)}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span className="font-medium text-blue-600">{localFilters.min_score || 0}%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Source Filter */}
        <Select
          label="Source"
          value={localFilters.source || ''}
          onChange={(e) => handleFilterChange('source', e.target.value || undefined)}
          options={[
            { value: '', label: 'All Sources' },
            { value: 'linkedin', label: 'LinkedIn' },
            { value: 'indeed', label: 'Indeed' },
            { value: 'glassdoor', label: 'Glassdoor' },
            { value: 'manual', label: 'Manual Entry' },
            { value: 'extension', label: 'Chrome Extension' },
          ]}
        />

        {/* Job Type Filter */}
        <Select
          label="Job Type"
          value={localFilters.job_type || ''}
          onChange={(e) => handleFilterChange('job_type', e.target.value || undefined)}
          options={[
            { value: '', label: 'All Types' },
            { value: 'full-time', label: 'Full-time' },
            { value: 'part-time', label: 'Part-time' },
            { value: 'contract', label: 'Contract' },
            { value: 'internship', label: 'Internship' },
          ]}
        />

        {/* Buttons */}
        <div className="flex gap-2 pt-4 border-t border-gray-200">
          <Button variant="primary" fullWidth onClick={applyFilters}>
            Apply Filters
          </Button>
          <Button variant="secondary" fullWidth onClick={resetFilters}>
            Reset
          </Button>
        </div>
      </div>
    </Card>
  );
}
