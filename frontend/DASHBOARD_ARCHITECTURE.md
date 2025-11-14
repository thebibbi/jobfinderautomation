# Web Dashboard Architecture

## Overview

Modern Next.js 14 dashboard with TypeScript, Tailwind CSS, and real-time WebSocket updates for the Job Automation System.

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **WebSocket**: Native WebSocket API with custom hook
- **Charts**: Recharts
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout with navigation
│   │   ├── page.tsx            # Dashboard home (overview)
│   │   ├── globals.css         # Global styles
│   │   ├── jobs/
│   │   │   └── page.tsx        # Jobs list page
│   │   ├── applications/
│   │   │   ├── page.tsx        # Applications list
│   │   │   └── [id]/
│   │   │       └── page.tsx    # Application detail
│   │   ├── recommendations/
│   │   │   └── page.tsx        # Recommended jobs
│   │   ├── interviews/
│   │   │   └── page.tsx        # Interviews & follow-ups
│   │   ├── analytics/
│   │   │   └── page.tsx        # Analytics dashboard
│   │   └── settings/
│   │       └── page.tsx        # Settings page
│   │
│   ├── components/             # Reusable React components
│   │   ├── layout/
│   │   │   ├── Navbar.tsx      # Top navigation bar
│   │   │   ├── Sidebar.tsx     # Side navigation
│   │   │   └── Footer.tsx      # Footer component
│   │   ├── dashboard/
│   │   │   ├── StatsCard.tsx   # Statistics card
│   │   │   ├── ActivityFeed.tsx # Recent activity
│   │   │   └── QuickActions.tsx # Quick action buttons
│   │   ├── jobs/
│   │   │   ├── JobCard.tsx     # Job listing card
│   │   │   ├── JobFilters.tsx  # Filter controls
│   │   │   └── JobDetails.tsx  # Job detail view
│   │   ├── applications/
│   │   │   ├── ApplicationCard.tsx        # Application card
│   │   │   ├── ApplicationTimeline.tsx   # Timeline view
│   │   │   ├── StatusBadge.tsx           # Status badge
│   │   │   └── UpdateStatusModal.tsx     # Status update modal
│   │   ├── recommendations/
│   │   │   └── RecommendationCard.tsx    # Recommendation card
│   │   ├── interviews/
│   │   │   ├── InterviewCard.tsx         # Interview card
│   │   │   ├── InterviewCalendar.tsx     # Calendar view
│   │   │   └── ScheduleModal.tsx         # Schedule modal
│   │   ├── analytics/
│   │   │   ├── FunnelChart.tsx           # Conversion funnel
│   │   │   ├── TrendChart.tsx            # Trend line chart
│   │   │   └── SuccessPatterns.tsx       # Success analysis
│   │   ├── common/
│   │   │   ├── Button.tsx                # Button component
│   │   │   ├── Card.tsx                  # Card container
│   │   │   ├── Modal.tsx                 # Modal dialog
│   │   │   ├── Badge.tsx                 # Badge component
│   │   │   ├── LoadingSpinner.tsx        # Loading indicator
│   │   │   └── Toast.tsx                 # Toast notification
│   │   └── ConnectionStatus.tsx          # WebSocket status
│   │
│   ├── lib/                    # Utilities and helpers
│   │   ├── api.ts              # API client with axios
│   │   ├── websocket.ts        # WebSocket manager
│   │   └── utils.ts            # Common utilities
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useWebSocket.ts     # WebSocket connection hook
│   │   ├── useJobs.ts          # Jobs data hook
│   │   ├── useApplications.ts  # Applications data hook
│   │   ├── useRecommendations.ts # Recommendations hook
│   │   ├── useInterviews.ts    # Interviews hook
│   │   └── useAnalytics.ts     # Analytics hook
│   │
│   └── types/                  # TypeScript type definitions
│       ├── job.ts              # Job types
│       ├── application.ts      # Application types
│       ├── interview.ts        # Interview types
│       └── websocket.ts        # WebSocket event types
│
├── public/                     # Static assets
│   ├── favicon.ico
│   └── logo.svg
│
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
├── Dockerfile
└── .env.local                  # Environment variables

```

## Key Features

### 1. Dashboard Home (`/`)

**Components**:
- Statistics cards (total jobs, applications, interviews, avg match score)
- Recent activity feed (last 10 events)
- Quick actions (add job, view recommendations)
- Upcoming interviews widget
- Follow-ups due widget
- Success metrics summary

**Data Sources**:
- `GET /api/v1/ats/statistics`
- `GET /api/v1/analytics/overview`
- WebSocket: Real-time updates

---

### 2. Jobs Page (`/jobs`)

**Components**:
- Job listing with cards
- Filters (status, match score, source)
- Search by company/title
- Sort options (date, match score)
- Pagination

**Features**:
- View job details in modal
- Update job status
- Analyze job on demand
- View skills gap analysis
- Quick apply actions

**Data Sources**:
- `GET /api/v1/jobs?status_filter={}&min_score={}&limit={}&skip={}`
- `POST /api/v1/analysis/jobs/{id}/analyze`
- `GET /api/v1/skills/analyze/{id}`

---

### 3. Applications Page (`/applications`)

**Components**:
- Kanban board view (saved, applied, interviewing, offer_received)
- List view with filters
- Application detail page (`/applications/{id}`)

**Features**:
- Drag-and-drop status updates
- Timeline view of all events
- Notes management
- Document generation
- Quick status updates

**Data Sources**:
- `GET /api/v1/jobs?status_filter={}`
- `POST /api/v1/ats/jobs/{id}/status`
- `GET /api/v1/ats/jobs/{id}/timeline`
- `POST /api/v1/ats/notes`

---

### 4. Recommendations Page (`/recommendations`)

**Components**:
- Recommended job cards with match scores
- Recommendation reasons
- Filter by min score
- Similar jobs suggestions

**Features**:
- One-click save to tracked jobs
- Dismiss with reason
- View full job details
- Learn from interactions

**Data Sources**:
- `GET /api/v1/recommendations?limit={}&algorithm={}&min_score={}`
- `POST /api/v1/recommendations/learn/click/{id}`
- `POST /api/v1/recommendations/learn/dismiss/{id}`

---

### 5. Interviews & Follow-ups Page (`/interviews`)

**Components**:
- Calendar view of upcoming interviews
- Interview cards with countdown
- Follow-ups due list
- Schedule interview modal

**Features**:
- Schedule new interview
- Update interview outcome
- Mark follow-up as sent
- View preparation notes
- Google Calendar sync indicator

**Data Sources**:
- `GET /api/v1/ats/interviews/upcoming?days_ahead={}`
- `POST /api/v1/ats/interviews`
- `PUT /api/v1/ats/interviews/{id}`
- `GET /api/v1/followup/due?hours_ahead={}`
- `POST /api/v1/followup/{id}/sent`

---

### 6. Analytics Page (`/analytics`)

**Components**:
- Overview statistics
- Conversion funnel chart
- Application trends over time
- Success patterns analysis
- Source performance comparison
- Match score distribution

**Features**:
- Date range selection
- Export data as CSV
- Success pattern insights
- Recommendations based on patterns

**Data Sources**:
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/funnel?start_date={}&end_date={}`
- `GET /api/v1/analytics/trends?metric={}&granularity={}`
- `GET /api/v1/analytics/success-patterns`

---

### 7. Settings Page (`/settings`)

**Components**:
- API configuration
- Profile settings
- Notification preferences
- Integration settings (Google Calendar, Drive)
- Cache management

**Features**:
- Test API connection
- Clear cache by namespace
- View connection statistics
- Export/import settings

**Data Sources**:
- `GET /api/v1/cache/stats`
- `DELETE /api/v1/cache/{namespace}`
- `GET /api/v1/connections` (WebSocket stats)

---

## Real-time Updates

### WebSocket Integration

**Connection**:
```typescript
const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
const ws = new WebSocket(`${wsUrl}/api/v1/ws?user_id={userId}&channels=jobs,applications,interviews,recommendations,skills,followups`);
```

**Event Handling**:
```typescript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'job.analyzed':
      // Refresh jobs list
      queryClient.invalidateQueries(['jobs']);
      // Show toast notification
      toast.success(`Job analyzed: ${message.data.match_score}% match`);
      break;

    case 'application.status_changed':
      // Refresh applications
      queryClient.invalidateQueries(['applications']);
      break;

    case 'interview.scheduled':
      // Refresh interviews
      queryClient.invalidateQueries(['interviews']);
      // Show notification
      toast.info(`Interview scheduled: ${message.data.interview_type}`);
      break;

    case 'recommendations.new':
      // Show badge on recommendations page
      setBadgeCount(message.data.count);
      break;
  }
};
```

---

## API Integration

### API Client (`src/lib/api.ts`)

```typescript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const jobsApi = {
  list: (params) => apiClient.get('/jobs', { params }),
  get: (id) => apiClient.get(`/jobs/${id}`),
  create: (data) => apiClient.post('/jobs', data),
  update: (id, data) => apiClient.patch(`/jobs/${id}`, data),
  delete: (id) => apiClient.delete(`/jobs/${id}`),
  process: (data) => apiClient.post('/jobs/process', data),
};

export const applicationsApi = {
  updateStatus: (id, data) => apiClient.post(`/ats/jobs/${id}/status`, data),
  getTimeline: (id) => apiClient.get(`/ats/jobs/${id}/timeline`),
  addNote: (data) => apiClient.post('/ats/notes', data),
};

export const recommendationsApi = {
  list: (params) => apiClient.get('/recommendations', { params }),
  learnClick: (id) => apiClient.post(`/recommendations/learn/click/${id}`),
  learnDismiss: (id, reason) => apiClient.post(`/recommendations/learn/dismiss/${id}`, { reason }),
};

export const interviewsApi = {
  upcoming: (params) => apiClient.get('/ats/interviews/upcoming', { params }),
  create: (data) => apiClient.post('/ats/interviews', data),
  update: (id, data) => apiClient.put(`/ats/interviews/${id}`, data),
};

export const analyticsApi = {
  overview: () => apiClient.get('/analytics/overview'),
  funnel: (params) => apiClient.get('/analytics/funnel', { params }),
  trends: (params) => apiClient.get('/analytics/trends', { params }),
  successPatterns: () => apiClient.get('/analytics/success-patterns'),
};
```

---

## Custom Hooks

### useWebSocket Hook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const socket = new WebSocket(
      `${wsUrl}/api/v1/ws?user_id=${userId}&channels=jobs,applications,interviews,recommendations,skills,followups`
    );

    socket.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    socket.onclose = () => {
      setIsConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    setWs(socket);
  }, [userId]);

  const handleMessage = useCallback((message: any) => {
    // Invalidate queries based on event type
    if (message.type.startsWith('job.')) {
      queryClient.invalidateQueries(['jobs']);
    }
    if (message.type.startsWith('application.')) {
      queryClient.invalidateQueries(['applications']);
    }
    if (message.type.startsWith('interview.')) {
      queryClient.invalidateQueries(['interviews']);
    }
    if (message.type.startsWith('recommendations.')) {
      queryClient.invalidateQueries(['recommendations']);
    }
  }, [queryClient]);

  useEffect(() => {
    connect();
    return () => {
      ws?.close();
    };
  }, [connect]);

  return { isConnected, ws };
}
```

---

## Styling System

### Tailwind CSS Configuration

**Color Palette**:
- Primary: Blue (#3b82f6)
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Danger: Red (#ef4444)
- Info: Purple (#8b5cf6)

**Component Patterns**:

```css
/* Card */
.card {
  @apply bg-white rounded-lg shadow-md p-6 border border-gray-200;
}

/* Badge */
.badge {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}

.badge-success {
  @apply bg-green-100 text-green-800;
}

.badge-warning {
  @apply bg-yellow-100 text-yellow-800;
}

/* Button */
.btn {
  @apply px-4 py-2 rounded-md font-medium transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-secondary {
  @apply bg-gray-200 text-gray-900 hover:bg-gray-300;
}
```

---

## State Management

### TanStack Query (React Query)

**Benefits**:
- Automatic caching
- Background refetching
- Optimistic updates
- Request deduplication
- Loading/error states

**Example Usage**:
```typescript
// useJobs.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi } from '@/lib/api';

export function useJobs(filters = {}) {
  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => jobsApi.list(filters),
    staleTime: 30000, // 30 seconds
  });
}

export function useUpdateJobStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }) => applicationsApi.updateStatus(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries(['jobs']);
      queryClient.invalidateQueries(['applications']);
    },
  });
}
```

---

## Performance Optimizations

1. **Code Splitting**: Next.js automatic code splitting per route
2. **Image Optimization**: Next.js Image component
3. **API Response Caching**: React Query with stale-while-revalidate
4. **WebSocket Reconnection**: Automatic with exponential backoff
5. **Lazy Loading**: Components loaded on demand
6. **Memoization**: React.memo for expensive components
7. **Virtual Scrolling**: For large lists (1000+ items)

---

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### Docker Compose Integration

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://backend:8000
    - NEXT_PUBLIC_WS_URL=ws://backend:8000
  depends_on:
    - backend
  networks:
    - job-automation
```

---

## Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Testing

### Unit Tests (Jest + React Testing Library)

```typescript
// __tests__/components/JobCard.test.tsx
import { render, screen } from '@testing-library/react';
import JobCard from '@/components/jobs/JobCard';

test('renders job card with match score', () => {
  const job = {
    id: 1,
    company: 'Google',
    job_title: 'Software Engineer',
    match_score: 85,
  };

  render(<JobCard job={job} />);

  expect(screen.getByText('Google')).toBeInTheDocument();
  expect(screen.getByText('85%')).toBeInTheDocument();
});
```

### E2E Tests (Playwright)

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('dashboard loads and shows statistics', async ({ page }) => {
  await page.goto('http://localhost:3000');

  await expect(page.locator('h1')).toContainText('Dashboard');
  await expect(page.locator('.stat-card')).toHaveCount(4);
});
```

---

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (responsive design)

---

## Accessibility

- ARIA labels on interactive elements
- Keyboard navigation support
- Focus indicators
- Screen reader friendly
- Color contrast WCAG AA compliant

---

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Export data (CSV, JSON, PDF)
- [ ] Batch operations (bulk status update)
- [ ] Advanced filtering with saved filters
- [ ] Custom dashboard widgets
- [ ] Collaborative features (share applications)
- [ ] Mobile app (React Native)
- [ ] Browser extension integration
- [ ] AI chat assistant
- [ ] Voice commands

---

## Documentation

- [API Reference](../docs/API_REFERENCE.md)
- [WebSocket Guide](../docs/WEBSOCKET_GUIDE.md)
- [Integration Guide](../docs/INTEGRATION_GUIDE.md)
- [Component Storybook](http://localhost:6006) (future)
