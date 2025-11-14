'use client';

import React, { useState } from 'react';
import Modal, { ModalFooter } from '@/components/common/Modal';
import Input, { Textarea } from '@/components/common/Input';
import Select from '@/components/common/Select';
import Button from '@/components/common/Button';

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobId: number;
  jobTitle: string;
  company: string;
  onSchedule: (data: InterviewData) => Promise<void>;
}

interface InterviewData {
  job_id: number;
  interview_type: string;
  scheduled_date: string;
  duration_minutes: number;
  location?: string;
  interviewer_name?: string;
  notes?: string;
}

export default function ScheduleModal({
  isOpen,
  onClose,
  jobId,
  jobTitle,
  company,
  onSchedule,
}: ScheduleModalProps) {
  const [formData, setFormData] = useState<InterviewData>({
    job_id: jobId,
    interview_type: 'phone_screen',
    scheduled_date: '',
    duration_minutes: 60,
    location: '',
    interviewer_name: '',
    notes: '',
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (field: keyof InterviewData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      await onSchedule(formData);
      onClose();
      setFormData({
        job_id: jobId,
        interview_type: 'phone_screen',
        scheduled_date: '',
        duration_minutes: 60,
        location: '',
        interviewer_name: '',
        notes: '',
      });
    } catch (error) {
      console.error('Failed to schedule interview:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const isValid = formData.scheduled_date && formData.interview_type;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Schedule Interview"
      size="lg"
    >
      <div className="space-y-4">
        {/* Job Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="font-semibold text-blue-900">{jobTitle}</p>
          <p className="text-sm text-blue-700">{company}</p>
        </div>

        {/* Interview Type */}
        <Select
          label="Interview Type"
          value={formData.interview_type}
          onChange={(e) => handleChange('interview_type', e.target.value)}
          options={[
            { value: 'phone_screen', label: 'Phone Screen' },
            { value: 'technical', label: 'Technical Interview' },
            { value: 'behavioral', label: 'Behavioral Interview' },
            { value: 'system_design', label: 'System Design' },
            { value: 'coding', label: 'Coding Interview' },
            { value: 'final', label: 'Final Round' },
            { value: 'other', label: 'Other' },
          ]}
        />

        {/* Date & Time */}
        <Input
          type="datetime-local"
          label="Date & Time"
          value={formData.scheduled_date}
          onChange={(e) => handleChange('scheduled_date', e.target.value)}
          required
        />

        {/* Duration */}
        <Select
          label="Duration"
          value={formData.duration_minutes.toString()}
          onChange={(e) => handleChange('duration_minutes', parseInt(e.target.value))}
          options={[
            { value: '30', label: '30 minutes' },
            { value: '45', label: '45 minutes' },
            { value: '60', label: '1 hour' },
            { value: '90', label: '1.5 hours' },
            { value: '120', label: '2 hours' },
            { value: '180', label: '3 hours' },
          ]}
        />

        {/* Location */}
        <Input
          label="Location / Meeting Link"
          placeholder="https://zoom.us/... or Office address"
          value={formData.location}
          onChange={(e) => handleChange('location', e.target.value)}
        />

        {/* Interviewer Name */}
        <Input
          label="Interviewer Name (optional)"
          placeholder="John Doe"
          value={formData.interviewer_name}
          onChange={(e) => handleChange('interviewer_name', e.target.value)}
        />

        {/* Notes */}
        <Textarea
          label="Notes (optional)"
          placeholder="Any preparation notes or important information..."
          value={formData.notes}
          onChange={(e) => handleChange('notes', e.target.value)}
          rows={3}
        />

        {/* Info */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <p className="text-sm text-green-800">
            <strong>Note:</strong> This interview will be automatically added to your Google Calendar
            with reminders set for 24 hours, 1 hour, and 15 minutes before.
          </p>
        </div>
      </div>

      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSubmit}
          isLoading={isLoading}
          disabled={!isValid}
        >
          Schedule Interview
        </Button>
      </ModalFooter>
    </Modal>
  );
}
