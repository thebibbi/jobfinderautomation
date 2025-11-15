'use client';

import React, { useState } from 'react';
import Modal, { ModalFooter } from '@/components/common/Modal';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Button from '@/components/common/Button';

interface ScrapeJobsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScrape: (data: ScrapeConfig) => Promise<void>;
}

interface ScrapeConfig {
  platform: string;
  keywords: string;
  location?: string;
  max_results?: number;
}

export default function ScrapeJobsModal({ isOpen, onClose, onScrape }: ScrapeJobsModalProps) {
  const [formData, setFormData] = useState<ScrapeConfig>({
    platform: 'linkedin',
    keywords: '',
    location: '',
    max_results: 20,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: keyof ScrapeConfig, value: any) => {
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

    if (!formData.keywords.trim()) {
      newErrors.keywords = 'Keywords are required';
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
      await onScrape(formData);
      onClose();
      // Reset form
      setFormData({
        platform: 'linkedin',
        keywords: '',
        location: '',
        max_results: 20,
      });
      setErrors({});
    } catch (error) {
      console.error('Failed to start scraping:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Scrape Jobs" size="md">
      <div className="space-y-4">
        {/* Platform */}
        <Select
          label="Platform"
          value={formData.platform}
          onChange={(e) => handleChange('platform', e.target.value)}
          options={[
            { value: 'linkedin', label: 'LinkedIn' },
            { value: 'indeed', label: 'Indeed' },
            { value: 'glassdoor', label: 'Glassdoor' },
          ]}
        />

        {/* Keywords */}
        <Input
          label="Search Keywords"
          placeholder="e.g., Software Engineer, Full Stack Developer"
          value={formData.keywords}
          onChange={(e) => handleChange('keywords', e.target.value)}
          error={errors.keywords}
          required
        />

        {/* Location */}
        <Input
          label="Location (optional)"
          placeholder="e.g., San Francisco, CA or Remote"
          value={formData.location}
          onChange={(e) => handleChange('location', e.target.value)}
        />

        {/* Max Results */}
        <Select
          label="Maximum Results"
          value={formData.max_results?.toString() || '20'}
          onChange={(e) => handleChange('max_results', parseInt(e.target.value))}
          options={[
            { value: '10', label: '10 jobs' },
            { value: '20', label: '20 jobs' },
            { value: '50', label: '50 jobs' },
            { value: '100', label: '100 jobs' },
          ]}
        />

        {/* Info Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Scraping will run in the background. You'll be notified when
            it's complete. New jobs will automatically appear in your jobs list.
          </p>
        </div>

        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-xs text-yellow-800">
            <strong>Important:</strong> Web scraping may be subject to rate limits and terms of
            service. Use responsibly.
          </p>
        </div>
      </div>

      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit} isLoading={isLoading}>
          Start Scraping
        </Button>
      </ModalFooter>
    </Modal>
  );
}
