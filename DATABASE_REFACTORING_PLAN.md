# Database Refactoring Plan - Tag-Flow V2

## Overview
This document outlines the planned database refactoring to eliminate unused fields, normalize data, and improve performance. The database can be quickly repopulated from scratch (<1s), so we don't need migration scripts - just schema changes and code updates.

## Fields to Remove/Change

### 🔴 HIGH IMPACT (Critical Changes)

#### 1. `creator_name` → `creator_id` (videos table)
**Current State:** `creator_name` field duplicates data from creators table
**Target:** Use `creator_id` with JOINs to creators table

**Code Impact:**
- **Database Schema:** `/mnt/d/tag-flow/src/database.py:59` - Remove creator_name, keep creator_id
- **Query Updates Needed:**
  - Lines 167, 423-433, 504-514: Filtering and search operations
  - Lines 246, 252-255, 326-327: INSERT operations  
  - Line 702: `get_unique_creators()` method
- **API Endpoints:** 
  - `/mnt/d/tag-flow/src/api/videos.py` - Update all filtering logic
  - `/mnt/d/tag-flow/src/api/creators.py` - Update creator queries
- **Frontend:** `/mnt/d/tag-flow/tag-flow-modern-ui-final/pages/GalleryPage.tsx` and `apiService.ts`

**Required Changes:**
1. Update all SELECT queries to use JOINs: `SELECT v.*, c.name as creator_name FROM videos v JOIN creators c ON v.creator_id = c.id`
2. Update filtering logic in API endpoints
3. Update external sources to resolve creator names to creator_id during population
4. Update frontend to handle creator data from JOINs

#### 2. `external_metadata` → Specific Columns (downloader_mapping table)
**Current State:** Stores giant JSON for 2-3 useful fields
**Target:** Extract to dedicated columns

**New Schema:**
```sql
ALTER TABLE downloader_mapping ADD COLUMN is_carousel_item BOOLEAN DEFAULT FALSE;
ALTER TABLE downloader_mapping ADD COLUMN carousel_order INTEGER;
ALTER TABLE downloader_mapping ADD COLUMN carousel_base_id TEXT;
-- Keep external_metadata initially, remove after migration
```

**Code Impact:**
- **Carousel Processing:** `/mnt/d/tag-flow/src/api/videos.py:111, 115-117, 145, 149-150`
- **External Sources:** `/mnt/d/tag-flow/src/external_sources.py:341, 370, 597`

**Required Changes:**
1. Update carousel detection logic to use new columns
2. Update external sources to populate specific fields
3. Extensive testing of carousel functionality

### 🟡 MEDIUM IMPACT

#### 3. `external_video_id` (videos table) - REMOVE
**Reason:** Redundant with `post_url`

**Code Impact:**
- Database Schema: `/mnt/d/tag-flow/src/database.py:56`
- Database Operations: Lines 299, 338, 311, 348, 575, 627
- External Sources: `/mnt/d/tag-flow/src/external_sources.py:335, 590, 848`
- Frontend: `/mnt/d/tag-flow/tag-flow-modern-ui-final/services/apiService.ts:61`

#### 4. Subscriptions Table Cleanup - REMOVE
- `creator_id` - Not used in frontend
- `external_id` - Never populated
- `metadata` - Never populated

### 🟢 LOW IMPACT (Easy Removals)

#### 5. `display_name` (creators table) - REMOVE
**Reason:** Exact duplicate of `name`

**Code Impact:**
- Database Schema: `/mnt/d/tag-flow/src/database.py:103`
- Operations: Lines 1083, 1087, 1089, external_sources.py:725, 746, 884, 898
- API: `creators.py:338`

#### 6. `source_path` (video_lists table) - REMOVE  
**Reason:** Never populated, frontend doesn't use

#### 7. `username` (creators_urls table) - REMOVE
**Reason:** Can extract from URLs when needed

## Implementation Strategy

### Phase 1: Easy Removals (Start Here)
1. Remove `display_name` - use `name` consistently
2. Remove `source_path` - update video list operations
3. Remove `username` - extract from URLs when needed
4. Remove unused subscriptions fields

### Phase 2: External Metadata Refactoring
1. Add new columns for carousel data
2. Update carousel processing logic
3. Update external sources population
4. Test carousel functionality thoroughly
5. Remove old external_metadata column

### Phase 3: Creator Name Normalization  
1. Update all queries to use JOINs with creators table
2. Update API endpoints to return creator data properly
3. Update frontend to handle creator data from JOINs
4. Remove creator_name field from videos table
5. Update external sources to use creator_id

## Database Schema Changes

### New Schema (Post-Refactoring)
```sql
-- videos table (simplified)
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    title TEXT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,              -- Keep: User wants to implement
    duration_seconds INTEGER,       -- Keep: User wants to implement  
    creator_id INTEGER NOT NULL,    -- Change: Use instead of creator_name
    platform TEXT NOT NULL,
    post_url TEXT,                  -- Keep: Primary URL field
    -- Remove: external_video_id (redundant)
    -- Remove: creator_name (use creator_id + JOIN)
    FOREIGN KEY (creator_id) REFERENCES creators(id)
);

-- creators table (simplified)  
CREATE TABLE creators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    -- Remove: display_name (duplicate)
);

-- video_lists table (simplified)
CREATE TABLE video_lists (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL,
    list_type TEXT NOT NULL,
    -- Remove: source_path (never used)
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- subscriptions table (simplified)
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    platform TEXT,
    subscription_url TEXT,
    -- Remove: creator_id (not used)
    -- Remove: external_id (never populated)
    -- Remove: metadata (never populated)
);

-- downloader_mapping table (optimized)
CREATE TABLE downloader_mapping (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL,
    external_path TEXT,
    is_carousel_item BOOLEAN DEFAULT FALSE,  -- New: Extract from JSON
    carousel_order INTEGER,                  -- New: Extract from JSON  
    carousel_base_id TEXT,                   -- New: Extract from JSON
    -- Remove: external_metadata (replace with specific fields)
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- creators_urls table (simplified)
CREATE TABLE creators_urls (
    id INTEGER PRIMARY KEY,
    creator_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    url TEXT NOT NULL,
    -- Remove: username (extract from URL when needed)
    FOREIGN KEY (creator_id) REFERENCES creators(id)
);
```

## Testing Checklist

### Critical Functionality to Test
- [ ] Carousel image grouping and display
- [ ] Creator filtering in gallery  
- [ ] Video loading and pagination
- [ ] Creator pages functionality
- [ ] Subscription pages functionality
- [ ] Video lists (favorites, liked, etc.)
- [ ] External sources population
- [ ] Admin operations

### Performance Testing
- [ ] Gallery page load times
- [ ] Creator search performance  
- [ ] Video filtering speed
- [ ] Database query optimization

## Notes
- Database can be repopulated quickly (<1s) so no need for complex migrations
- Focus on code changes rather than data migration scripts
- Test carousel functionality extensively - this is the most complex part
- External sources population logic needs updates for creator_id resolution

## Files That Need Major Updates
- `/mnt/d/tag-flow/src/database.py` - Schema and query updates
- `/mnt/d/tag-flow/src/api/videos.py` - Carousel processing logic
- `/mnt/d/tag-flow/src/api/creators.py` - Creator query updates  
- `/mnt/d/tag-flow/src/external_sources.py` - Population logic updates
- `/mnt/d/tag-flow/tag-flow-modern-ui-final/services/apiService.ts` - Type definitions
- `/mnt/d/tag-flow/tag-flow-modern-ui-final/pages/GalleryPage.tsx` - Creator filtering

## Risk Assessment
- **High Risk:** Carousel functionality (external_metadata changes)
- **Medium Risk:** Creator filtering (creator_name changes)
- **Low Risk:** Field removals (display_name, source_path, etc.)