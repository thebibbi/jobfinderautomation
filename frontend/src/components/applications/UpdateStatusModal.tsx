'use client';

import React, { useState } from 'react';
import Modal, { ModalFooter } from '@/components/common/Modal';
import Select from '@/components/common/Select';
import { Textarea } from '@/components/common/Input';
import Button from '@/components/common/Button';

interface UpdateStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentStatus: string;
  onUpdate: (status: string, notes?: string) => Promise<void>;
}

export default function UpdateStatusModal({
  isOpen,
  onClose,
  currentStatus,
  onUpdate,
}: UpdateStatusModalProps) {
  const [newStatus, setNewStatus] = useState(currentStatus);
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      await onUpdate(newStatus, notes || undefined);
      onClose();
      setNotes('');
    } catch (error) {
      console.error('Failed to update status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statusOptions = [
    { value: 'saved', label: 'Saved' },
    { value: 'applied', label: 'Applied' },
    { value: 'screening', label: 'Screening' },
    { value: 'interviewing', label: 'Interviewing' },
    { value: 'technical_assessment', label: 'Technical Assessment' },
    { value: 'offer_received', label: 'Offer Received' },
    { value: 'accepted', label: 'Accepted' },
    { value: 'rejected', label: 'Rejected' },
    { value: 'withdrawn', label: 'Withdrawn' },
    { value: 'archived', label: 'Archived' },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Update Application Status"
      size="md"
    >
      <div className="space-y-4">
        <Select
          label="New Status"
          value={newStatus}
          onChange={(e) => setNewStatus(e.target.value)}
          options={statusOptions}
        />

        <Textarea
          label="Notes (optional)"
          placeholder="Add any relevant notes about this status change..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
        />

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Updating to certain statuses will trigger automated actions:
          </p>
          <ul className="mt-2 text-xs text-blue-700 list-disc list-inside space-y-1">
            <li>Applied → Schedules follow-up reminders</li>
            <li>Interviewing → Creates calendar events</li>
            <li>Offer Received → Notifies recommendation engine</li>
          </ul>
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
          disabled={newStatus === currentStatus && !notes}
        >
          Update Status
        </Button>
      </ModalFooter>
    </Modal>
  );
}
