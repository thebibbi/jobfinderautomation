'use client';

import React, { useState } from 'react';
import Modal, { ModalFooter } from '@/components/common/Modal';
import Input, { Textarea } from '@/components/common/Input';
import Select from '@/components/common/Select';
import Button from '@/components/common/Button';
import { JobCreate } from '@/types/job';

interface AddJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (data: JobCreate) => Promise<void>;
}

export default function AddJobModal({ isOpen, onClose, onAdd }: AddJobModalProps) {
  const [formData, setFormData] = useState<JobCreate>({
    company: '',
    job_title: '',
    job_description: '',
    job_url: '',
    location: '',
    salary_min: undefined,
    salary_max: undefined,
    source: 'manual',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof JobCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.company.trim()) {
      newErrors.company = 'Company name is required';
    }
    if (!formData.job_title.trim()) {
      newErrors.job_title = 'Job title is required';
    }
    if (!formData.job_description.trim()) {
      newErrors.job_description = 'Job description is required';
    }
    if (formData.job_url && !formData.job_url.match(/^https?:\/\/.+/)) {
      newErrors.job_url = 'Please enter a valid URL';
    }
    if (formData.salary_min && formData.salary_max && formData.salary_min > formData.salary_max) {
      newErrors.salary_max = 'Maximum salary must be greater than minimum';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      await onAdd(formData);
      onClose();
      // Reset form
      setFormData({
        company: '',
        job_title: '',
        job_description: '',
        job_url: '',
        location: '',
        salary_min: undefined,
        salary_max: undefined,
        source: 'manual',
      });
      setErrors({});
    } catch (error) {
      console.error('Failed to add job:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Job" size="lg">
      <div className="space-y-4">
        {/* Company */}
        <Input
          label="Company"
          placeholder="e.g., Google, Microsoft, Apple"
          value={formData.company}
          onChange={(e) => handleChange('company', e.target.value)}
          error={errors.company}
          required
        />

        {/* Job Title */}
        <Input
          label="Job Title"
          placeholder="e.g., Senior Software Engineer"
          value={formData.job_title}
          onChange={(e) => handleChange('job_title', e.target.value)}
          error={errors.job_title}
          required
        />

        {/* Job Description */}
        <Textarea
          label="Job Description"
          placeholder="Paste the full job description here..."
          value={formData.job_description}
          onChange={(e) => handleChange('job_description', e.target.value)}
          error={errors.job_description}
          rows={8}
          required
        />

        {/* Job URL */}
        <Input
          label="Job URL (optional)"
          placeholder="https://company.com/careers/job-123"
          value={formData.job_url}
          onChange={(e) => handleChange('job_url', e.target.value)}
          error={errors.job_url}
        />

        {/* Location */}
        <Input
          label="Location (optional)"
          placeholder="e.g., San Francisco, CA or Remote"
          value={formData.location}
          onChange={(e) => handleChange('location', e.target.value)}
        />

        {/* Salary Range */}
        <div className="grid grid-cols-2 gap-4">
          <Input
            type="number"
            label="Minimum Salary (optional)"
            placeholder="80000"
            value={formData.salary_min || ''}
            onChange={(e) =>
              handleChange('salary_min', e.target.value ? parseInt(e.target.value) : undefined)
            }
          />
          <Input
            type="number"
            label="Maximum Salary (optional)"
            placeholder="120000"
            value={formData.salary_max || ''}
            onChange={(e) =>
              handleChange('salary_max', e.target.value ? parseInt(e.target.value) : undefined)
            }
            error={errors.salary_max}
          />
        </div>

        {/* Source */}
        <Select
          label="Source"
          value={formData.source}
          onChange={(e) => handleChange('source', e.target.value)}
          options={[
            { value: 'manual', label: 'Manual Entry' },
            { value: 'linkedin', label: 'LinkedIn' },
            { value: 'indeed', label: 'Indeed' },
            { value: 'glassdoor', label: 'Glassdoor' },
            { value: 'company_website', label: 'Company Website' },
            { value: 'referral', label: 'Referral' },
            { value: 'recruiter', label: 'Recruiter' },
            { value: 'other', label: 'Other' },
          ]}
        />

        {/* Info Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> After adding the job, you can analyze it with AI to get match
            scoring and personalized insights.
          </p>
        </div>
      </div>

      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit} isLoading={isLoading}>
          Add Job
        </Button>
      </ModalFooter>
    </Modal>
  );
}
