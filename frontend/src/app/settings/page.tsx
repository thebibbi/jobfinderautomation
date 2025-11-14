'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Input, { Textarea } from '@/components/common/Input';
import Select from '@/components/common/Select';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import { useToast } from '@/components/common/Toast';

export default function SettingsPage() {
  const { showToast } = useToast();
  const [isSaving, setIsSaving] = useState(false);

  // Profile Settings
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    phone: '',
    location: '',
    resume_url: '',
    linkedin_url: '',
    github_url: '',
  });

  // Notification Settings
  const [notifications, setNotifications] = useState({
    email_new_recommendations: true,
    email_interview_reminders: true,
    email_follow_up_reminders: true,
    push_new_recommendations: false,
    push_interview_reminders: true,
  });

  // Job Preferences
  const [preferences, setPreferences] = useState({
    job_types: ['full-time'],
    locations: ['remote'],
    salary_min: 100000,
    salary_max: 200000,
    industries: [] as string[],
  });

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      // API call to save profile
      await new Promise((resolve) => setTimeout(resolve, 1000));
      showToast('success', 'Profile updated successfully');
    } catch (error) {
      showToast('error', 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">Manage your account and preferences</p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Full Name"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                placeholder="John Doe"
              />
              <Input
                label="Email"
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                placeholder="john@example.com"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Phone"
                type="tel"
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                placeholder="+1 (555) 123-4567"
              />
              <Input
                label="Location"
                value={profile.location}
                onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                placeholder="San Francisco, CA"
              />
            </div>

            <Input
              label="Resume URL"
              value={profile.resume_url}
              onChange={(e) => setProfile({ ...profile, resume_url: e.target.value })}
              placeholder="https://drive.google.com/..."
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="LinkedIn URL"
                value={profile.linkedin_url}
                onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
                placeholder="https://linkedin.com/in/..."
              />
              <Input
                label="GitHub URL"
                value={profile.github_url}
                onChange={(e) => setProfile({ ...profile, github_url: e.target.value })}
                placeholder="https://github.com/..."
              />
            </div>

            <div className="flex justify-end">
              <Button variant="primary" onClick={handleSaveProfile} isLoading={isSaving}>
                Save Profile
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Job Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>Job Preferences</CardTitle>
          <p className="text-sm text-gray-600 mt-1">
            Help us recommend better jobs by setting your preferences
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Types
              </label>
              <div className="flex flex-wrap gap-2">
                {['full-time', 'part-time', 'contract', 'internship'].map((type) => (
                  <Badge
                    key={type}
                    variant={preferences.job_types.includes(type) ? 'info' : 'default'}
                    className="cursor-pointer"
                  >
                    {type.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Minimum Salary"
                type="number"
                value={preferences.salary_min}
                onChange={(e) =>
                  setPreferences({ ...preferences, salary_min: parseInt(e.target.value) })
                }
              />
              <Input
                label="Maximum Salary"
                type="number"
                value={preferences.salary_max}
                onChange={(e) =>
                  setPreferences({ ...preferences, salary_max: parseInt(e.target.value) })
                }
              />
            </div>

            <div className="flex justify-end">
              <Button variant="primary" onClick={handleSaveProfile}>
                Save Preferences
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Email Notifications</p>
                  <p className="text-sm text-gray-600">Receive updates via email</p>
                </div>
              </div>

              <div className="ml-4 space-y-3">
                {[
                  { key: 'email_new_recommendations', label: 'New job recommendations' },
                  { key: 'email_interview_reminders', label: 'Interview reminders' },
                  { key: 'email_follow_up_reminders', label: 'Follow-up reminders' },
                ].map((item) => (
                  <label key={item.key} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifications[item.key as keyof typeof notifications]}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          [item.key]: e.target.checked,
                        })
                      }
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <span className="text-sm text-gray-700">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-gray-200">
              <Button variant="primary" onClick={handleSaveProfile}>
                Save Notifications
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Integration Status */}
      <Card>
        <CardHeader>
          <CardTitle>Integrations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Google Calendar</p>
                  <p className="text-sm text-gray-600">Sync interviews to your calendar</p>
                </div>
              </div>
              <Badge variant="success">Connected</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Google Drive</p>
                  <p className="text-sm text-gray-600">Store documents and resumes</p>
                </div>
              </div>
              <Badge variant="success">Connected</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
