'use client';

import React, { useState } from 'react';
import { DndProvider, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import ApplicationCard from '@/components/applications/ApplicationCard';
import UpdateStatusModal from '@/components/applications/UpdateStatusModal';
import { Card } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { LoadingPage } from '@/components/common/LoadingSpinner';
import { useApplications, useApplicationsList, useUpdateStatus } from '@/hooks/useApplications';
import { useToast } from '@/components/common/Toast';

const STATUSES = [
  { key: 'saved', label: 'Saved', color: 'bg-gray-100' },
  { key: 'applied', label: 'Applied', color: 'bg-blue-100' },
  { key: 'screening', label: 'Screening', color: 'bg-indigo-100' },
  { key: 'interviewing', label: 'Interviewing', color: 'bg-purple-100' },
  { key: 'offer_received', label: 'Offer', color: 'bg-green-100' },
  { key: 'rejected', label: 'Rejected', color: 'bg-red-100' },
];

function KanbanColumn({ status, applications, onCardClick, onDrop }: any) {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'APPLICATION',
    drop: (item: any) => onDrop(item.id, status.key),
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  }));

  return (
    <div
      ref={drop as any}
      className={`flex-shrink-0 w-80 ${isOver ? 'ring-2 ring-blue-500' : ''}`}
    >
      <div className={`rounded-lg ${status.color} p-3 mb-3`}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{status.label}</h3>
          <Badge variant="default" size="sm">
            {applications.length}
          </Badge>
        </div>
      </div>

      <div className="space-y-3">
        {applications.map((app: any) => (
          <ApplicationCard
            key={app.id}
            application={app}
            onClick={() => onCardClick(app)}
          />
        ))}
        {applications.length === 0 && (
          <Card padding="sm">
            <p className="text-sm text-gray-500 text-center py-8">
              No applications
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function ApplicationsPage() {
  const [selectedApp, setSelectedApp] = useState<any>(null);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const { data: stats, isLoading: statsLoading } = useApplications();
  const { data: applicationsData, isLoading: appsLoading, error: appsError } = useApplicationsList();
  const updateStatus = useUpdateStatus();
  const { showToast } = useToast();

  if (statsLoading || appsLoading) {
    return <LoadingPage text="Loading applications..." />;
  }

  // Use real applications data from API
  const applications = applicationsData?.applications || [];

  const applicationsByStatus = STATUSES.reduce((acc, status) => {
    acc[status.key] = applications.filter((app: any) => app.status === status.key);
    return acc;
  }, {} as Record<string, any[]>);

  const handleCardClick = (app: any) => {
    setSelectedApp(app);
    setIsStatusModalOpen(true);
  };

  const handleDrop = async (appId: number, newStatus: string) => {
    try {
      await updateStatus.mutateAsync({
        jobId: appId,
        status: { status: newStatus },
      });
      showToast('success', 'Application status updated');
    } catch (error) {
      showToast('error', 'Failed to update status');
    }
  };

  const handleUpdateStatus = async (newStatus: string, notes?: string) => {
    if (!selectedApp) return;

    try {
      await updateStatus.mutateAsync({
        jobId: selectedApp.id,
        status: { status: newStatus, notes },
      });
      showToast('success', 'Application status updated');
      setIsStatusModalOpen(false);
    } catch (error) {
      showToast('error', 'Failed to update status');
      throw error;
    }
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Applications</h1>
          <p className="mt-2 text-gray-600">
            Track your applications through the hiring process
          </p>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          {STATUSES.map((status) => (
            <Card key={status.key} padding="sm">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">
                  {applicationsByStatus[status.key]?.length || 0}
                </p>
                <p className="text-xs text-gray-600 mt-1">{status.label}</p>
              </div>
            </Card>
          ))}
        </div>

        {/* Kanban Board */}
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 min-w-max">
            {STATUSES.map((status) => (
              <KanbanColumn
                key={status.key}
                status={status}
                applications={applicationsByStatus[status.key] || []}
                onCardClick={handleCardClick}
                onDrop={handleDrop}
              />
            ))}
          </div>
        </div>

        {/* Empty State */}
        {applications.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No applications yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start by adding jobs and applying to them.
            </p>
          </div>
        )}

        {/* Update Status Modal */}
        {selectedApp && (
          <UpdateStatusModal
            isOpen={isStatusModalOpen}
            onClose={() => setIsStatusModalOpen(false)}
            currentStatus={selectedApp.status}
            onUpdate={handleUpdateStatus}
          />
        )}
      </div>
    </DndProvider>
  );
}
