'use client';

import React, { useState, useEffect } from 'react';
import Modal, { ModalFooter } from '@/components/common/Modal';
import Button from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { jobsApi } from '@/lib/api';

interface ImportFromDriveModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (fileId: string) => Promise<void>;
}

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  createdTime: string;
  modifiedTime: string;
  webViewLink: string;
  size?: string;
}

export default function ImportFromDriveModal({
  isOpen,
  onClose,
  onImport,
}: ImportFromDriveModalProps) {
  const [files, setFiles] = useState<DriveFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<string>('');
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadFiles();
    }
  }, [isOpen]);

  const loadFiles = async () => {
    setIsLoading(true);
    try {
      const response = await jobsApi.listDriveFiles();
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async () => {
    if (!selectedFileId) return;

    setIsImporting(true);
    try {
      await onImport(selectedFileId);
      onClose();
      setSelectedFileId('');
    } catch (error) {
      console.error('Failed to import:', error);
    } finally {
      setIsImporting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Import from Google Drive" size="lg">
      <div className="space-y-4">
        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Select a job description</strong> from your Google Drive to import. The system
            will use AI to extract job details and create a job record.
          </p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" text="Loading files from Drive..." />
          </div>
        )}

        {/* Files List */}
        {!isLoading && files.length > 0 && (
          <div className="max-h-96 overflow-y-auto space-y-2">
            {files.map((file) => (
              <div
                key={file.id}
                className={`border rounded-lg p-3 cursor-pointer transition-all ${
                  selectedFileId === file.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => setSelectedFileId(file.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900 text-sm">{file.name}</h4>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-600">
                      <span>Modified: {formatDate(file.modifiedTime)}</span>
                      {file.size && <span>Size: {(parseInt(file.size) / 1024).toFixed(1)} KB</span>}
                    </div>
                  </div>
                  {selectedFileId === file.id && (
                    <svg
                      className="w-5 h-5 text-blue-600 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && files.length === 0 && (
          <div className="text-center py-8">
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
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No files found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No Google Docs found in your configured Drive folder.
            </p>
            <div className="mt-4">
              <Button variant="secondary" onClick={loadFiles}>
                Refresh
              </Button>
            </div>
          </div>
        )}

        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-xs text-yellow-800">
            <strong>Note:</strong> Make sure the file is a Google Doc containing a job description.
            The AI will attempt to extract company, title, location, and description.
          </p>
        </div>
      </div>

      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={isImporting}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleImport}
          isLoading={isImporting}
          disabled={!selectedFileId || isImporting}
        >
          Import Selected File
        </Button>
      </ModalFooter>
    </Modal>
  );
}
