'use client';

import React, { useState, useRef } from 'react';
import Modal, { ModalFooter } from '@/components/common/Modal';
import Button from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { jobsApi } from '@/lib/api';

interface UploadJDModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (jobId: number) => void;
}

export default function UploadJDModal({
  isOpen,
  onClose,
  onUploadSuccess,
}: UploadJDModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedTypes = ['.docx', '.pdf', '.md', '.markdown'];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize) {
      return `File size must be less than ${maxFileSize / (1024 * 1024)}MB`;
    }

    // Check file type
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      return `Invalid file type. Allowed: ${allowedTypes.join(', ')}`;
    }

    return null;
  };

  const handleFileSelect = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }

    setError('');
    setSelectedFile(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError('');

    try {
      // Simulate progress (FastAPI doesn't provide upload progress easily)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await jobsApi.uploadJD(selectedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Extract job ID from response
      const jobId = response.data?.job_id;

      if (jobId) {
        setTimeout(() => {
          onUploadSuccess(jobId);
          handleClose();
        }, 500);
      } else {
        throw new Error('No job ID returned from server');
      }
    } catch (error: any) {
      console.error('Upload failed:', error);
      setError(
        error.response?.data?.detail ||
        'Failed to upload job description. Please try again.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setError('');
    setUploadProgress(0);
    setIsUploading(false);
    setIsDragging(false);
    onClose();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Upload Job Description" size="lg">
      <div className="space-y-4">
        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Upload a job description</strong> in DOCX, PDF, or Markdown format.
            The system will convert it to Markdown, extract job details using AI, and
            upload it to Google Drive.
          </p>
        </div>

        {/* File Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : selectedFile
              ? 'border-green-500 bg-green-50'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={allowedTypes.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
          />

          {!selectedFile ? (
            <div>
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
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="mt-2 text-sm font-medium text-gray-700">
                Drag and drop your job description here
              </p>
              <p className="mt-1 text-xs text-gray-500">or</p>
              <Button
                variant="secondary"
                size="sm"
                className="mt-2"
                onClick={() => fileInputRef.current?.click()}
              >
                Browse Files
              </Button>
              <p className="mt-3 text-xs text-gray-500">
                Supported: {allowedTypes.join(', ')} (max {maxFileSize / (1024 * 1024)}MB)
              </p>
            </div>
          ) : (
            <div>
              <svg
                className="mx-auto h-12 w-12 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="mt-2 text-sm font-medium text-gray-900">
                {selectedFile.name}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {formatFileSize(selectedFile.size)}
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2"
                onClick={() => {
                  setSelectedFile(null);
                  setError('');
                }}
                disabled={isUploading}
              >
                Choose Different File
              </Button>
            </div>
          )}
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-700">Uploading and processing...</span>
              <span className="text-gray-500">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 text-center">
              Converting to Markdown and extracting job details...
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <svg
                className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Processing Info */}
        <div className="bg-gray-50 rounded-lg p-3 space-y-2">
          <p className="text-xs font-medium text-gray-700">What happens next:</p>
          <ul className="text-xs text-gray-600 space-y-1 ml-4 list-disc">
            <li>File is converted to Markdown format</li>
            <li>AI extracts company name, job title, and details</li>
            <li>Google Drive folder is created for the job</li>
            <li>Markdown JD is uploaded to the Drive folder</li>
            <li>Job analysis and document generation are triggered</li>
          </ul>
        </div>
      </div>

      <ModalFooter>
        <Button variant="ghost" onClick={handleClose} disabled={isUploading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
        >
          {isUploading ? (
            <>
              <LoadingSpinner size="sm" className="mr-2" />
              Uploading...
            </>
          ) : (
            'Upload & Process'
          )}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
