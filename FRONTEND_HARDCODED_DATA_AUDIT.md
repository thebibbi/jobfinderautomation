# Frontend Hardcoded Data Audit & Fix Plan

## 🔍 Issues Found

### 1. **Dashboard Page** (`app/page.tsx`)
**Line 25-35:** Mock activity data
```typescript
// Mock activity data - in real app, this would come from an API
const activities = [
  {
    id: 1,
    type: 'job_added' as const,
    title: 'New job added',
    description: 'Senior Software Engineer position',
    timestamp: new Date().toISOString(),
    metadata: { company: 'Google' },
  },
];
```
**Status:** ❌ HARDCODED
**Fix Required:** Create `useActivities()` hook to fetch from API

---

### 2. **Applications Page** (`app/applications/page.tsx`)
**Line 77-78:** Empty mock applications array
```typescript
// Mock applications data - in real app, this would come from API
const applications: any[] = [];
```
**Status:** ❌ HARDCODED (empty array)
**Fix Required:** Use `useApplications()` hook properly to fetch real data

---

### 3. **Settings Page** (`app/settings/page.tsx`)
**Status:** ✅ FIXED
- Integration statuses now fetched from API
- Proper error handling implemented
- No hardcoded statuses

---

## 📋 Complete Fix Checklist

### Pages to Fix:
- [x] Settings Page - Integration statuses
- [ ] Dashboard Page - Activity feed data
- [ ] Applications Page - Applications list
- [ ] Analytics Page - Check for hardcoded data
- [ ] Interviews Page - Check for hardcoded data
- [ ] Recommendations Page - Check for hardcoded data
- [ ] Jobs Page - Check for hardcoded data
- [ ] Job Detail Page - Check for hardcoded data

### Components to Check:
- [ ] ActivityFeed - Ensure it handles empty/error states
- [ ] StatsCard - Check if "change" values are hardcoded
- [ ] QuickActions - Already uses API ✅
- [ ] Navbar - WebSocket status (dynamic) ✅

---

## 🎯 Fix Strategy

### 1. Create Missing Hooks
```typescript
// hooks/useActivities.ts
export function useActivities(limit?: number) {
  return useQuery({
    queryKey: ['activities', limit],
    queryFn: async () => {
      const response = await apiClient.get('/activities', {
        params: { limit }
      });
      return response.data;
    },
    staleTime: 30000, // 30 seconds
  });
}
```

### 2. Update Dashboard Page
```typescript
// Before
const activities = [/* hardcoded */];

// After
const { data: activities, isLoading: activitiesLoading } = useActivities(10);
const safeActivities = activities || [];
```

### 3. Update Applications Page
```typescript
// Before
const applications: any[] = [];

// After
const { data: applications, isLoading } = useApplicationsList();
const safeApplications = applications || [];
```

### 4. Add Error States
Every data fetch should have:
- Loading state
- Error state with retry button
- Empty state with helpful message
- Success state with data

---

## 🚨 Critical Rules

### Never Hardcode:
1. ❌ Service connection statuses
2. ❌ User data
3. ❌ Activity/event data
4. ❌ Statistics or counts
5. ❌ Application statuses
6. ❌ Job listings
7. ❌ Integration states

### Always Dynamic:
1. ✅ Fetch from API
2. ✅ Show loading states
3. ✅ Handle errors gracefully
4. ✅ Provide retry mechanisms
5. ✅ Show empty states
6. ✅ Cache appropriately

### Acceptable Hardcoded:
1. ✅ UI text/labels
2. ✅ Icon SVGs
3. ✅ Color schemes
4. ✅ Layout configurations
5. ✅ Status type definitions (enums)

---

## 📊 Data Flow Pattern

```
API Endpoint → Hook → Component → UI
     ↓          ↓         ↓        ↓
  /activities  useActivities  Dashboard  ActivityFeed
  /integrations useIntegrations Settings  IntegrationCard
  /applications useApplications Apps     ApplicationCard
```

---

## 🔧 Implementation Plan

### Phase 1: Create Hooks ✅
- [x] useIntegrations
- [ ] useActivities
- [ ] useApplicationsList (enhance existing)

### Phase 2: Update Pages
- [ ] Dashboard - Activity feed
- [ ] Applications - Applications list
- [ ] Check remaining pages

### Phase 3: Add Error Handling
- [ ] Loading spinners
- [ ] Error banners
- [ ] Retry buttons
- [ ] Empty states

### Phase 4: Testing
- [ ] Test with API down
- [ ] Test with empty data
- [ ] Test with errors
- [ ] Test with real data

---

## 📝 Backend API Requirements

### Endpoints Needed:
1. `GET /api/v1/activities` - Recent activity feed
   ```json
   {
     "activities": [
       {
         "id": 1,
         "type": "job_added",
         "title": "New job added",
         "description": "...",
         "timestamp": "2025-11-15T13:00:00Z",
         "metadata": {}
       }
     ]
   }
   ```

2. `GET /api/v1/applications` - List all applications
   ```json
   {
     "applications": [
       {
         "id": 1,
         "job_id": 123,
         "status": "applied",
         "applied_at": "2025-11-15T13:00:00Z",
         "company": "...",
         "position": "..."
       }
     ]
   }
   ```

3. `GET /api/v1/integrations/status` - Integration statuses ✅ (Already implemented)

---

## ✅ Success Criteria

A page is properly implemented when:
1. ✅ No hardcoded data (except UI constants)
2. ✅ All data fetched from API
3. ✅ Loading states shown
4. ✅ Errors handled gracefully
5. ✅ Empty states displayed
6. ✅ Retry mechanisms available
7. ✅ Type-safe implementation
8. ✅ Proper caching configured

---

## 🎯 Priority Order

1. **High Priority** (User-facing status):
   - [x] Settings - Integration statuses
   - [ ] Dashboard - Activity feed
   - [ ] Applications - Application list

2. **Medium Priority** (Data display):
   - [ ] Analytics - Charts/stats
   - [ ] Interviews - Interview list
   - [ ] Recommendations - Recommendation list

3. **Low Priority** (Already mostly dynamic):
   - [ ] Jobs - Job list (already uses API)
   - [ ] Job Detail - Job details (already uses API)

---

## 📚 Reference Implementation

See `app/settings/page.tsx` for the correct pattern:
- ✅ Uses `useIntegrations()` hook
- ✅ Shows loading spinner
- ✅ Displays error banner
- ✅ Shows individual service status
- ✅ Handles API failures gracefully
- ✅ Provides retry mechanism
- ✅ Type-safe implementation
