# GitHub Actions Workflow Integration Guide

**Date**: 2025-10-04  
**Workflow**: Kritis V4.0 - PROD10 Final AI Legal Document Analysis  
**File**: `.github/workflows/kritis-analysis.yml`

---

## 📋 Workflow Overview

The GitHub Actions workflow provides automated legal document analysis using the Kritis V4.0 PROD10 pipeline with enhanced features including:
- Constitutional document detection
- Source translation integration
- Background job status tracking
- Date intelligence
- Category suggestions

---

## 🚀 Workflow Inputs

### Required Inputs

#### 1. `source_id` (Required)
- **Type**: String
- **Format**: UUID
- **Description**: The UUID of the source document to analyze
- **Example**: `d7eaa191-fd7b-48ef-9013-33579398d6ad`

#### 2. `pipeline_stage` (Required)
- **Type**: Choice
- **Default**: `v40-complete`
- **Description**: The pipeline stage to execute

**Available Options**:

| Option | Description | Use Case |
|--------|-------------|----------|
| `v40-complete` | Complete V4.0 PROD10 pipeline (all 4 stages) | **Recommended** - Full analysis from start to finish |
| `v40-extract` | Stage 1: Enhanced extraction with preamble | Rerun extraction only |
| `v40-analyze` | Stage 2: Definitive analysis with V4.2 prompts | Rerun analysis only |
| `v40-synthesize` | Stage 3: Final summary synthesis | Rerun synthesis only |
| `v40-ingest` | Stage 4: Definitive law ingestion | Rerun ingestion only |
| `v31-complete` | Complete V3.1 PROD9 pipeline (legacy) | Legacy support |
| `validate-environment` | Environment validation only | Testing/debugging |

### Optional Inputs

#### 3. `job_id` (Optional) ⭐ NEW
- **Type**: String
- **Format**: UUID
- **Description**: Background job ID for real-time status tracking
- **Example**: `550e8400-e29b-41d4-a716-446655440000`
- **When to use**: Pass this when triggering from Next.js app for real-time notifications

---

## 📡 Integration with Next.js App

### Step 1: Create Background Job

In your Next.js app, first create a background job record:

```typescript
// Next.js API Route or Server Action
import { createClient } from '@/lib/supabase/server';

async function triggerAnalysis(sourceId: string, userId: string) {
  const supabase = createClient();
  
  // Create background job using Supabase function
  const { data: job, error } = await supabase.rpc('create_new_job', {
    p_job_type: 'KRITIS_V40_ANALYSIS',
    p_payload: { source_id: sourceId },
    p_triggered_by: userId
  });
  
  if (error) throw error;
  
  return job.id; // This is your job_id
}
```

### Step 2: Trigger GitHub Actions Workflow

Use GitHub's REST API or Octokit to trigger the workflow:

```typescript
import { Octokit } from '@octokit/rest';

async function triggerGitHubWorkflow(sourceId: string, jobId: string) {
  const octokit = new Octokit({
    auth: process.env.GITHUB_TOKEN // Fine-grained token with workflow dispatch
  });
  
  await octokit.actions.createWorkflowDispatch({
    owner: 'gammadev-y',
    repo: 'agora_kritis',
    workflow_id: 'kritis-analysis.yml',
    ref: 'master',
    inputs: {
      source_id: sourceId,
      job_id: jobId, // ⭐ Pass job_id for status tracking
      pipeline_stage: 'v40-complete'
    }
  });
  
  return jobId;
}
```

### Step 3: Listen for Real-Time Updates

Use Supabase Realtime to listen for job status changes:

```typescript
// In your React component
import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';

function useJobStatus(jobId: string) {
  const [status, setStatus] = useState<'PENDING' | 'SUCCESS' | 'FAILED'>('PENDING');
  const [message, setMessage] = useState<string>('');
  
  useEffect(() => {
    const supabase = createClient();
    
    // Subscribe to changes on the specific job
    const channel = supabase
      .channel(`job-${jobId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'agora',
          table: 'background_jobs',
          filter: `id=eq.${jobId}`
        },
        (payload) => {
          setStatus(payload.new.status);
          setMessage(payload.new.result_message);
          
          // Notify user
          if (payload.new.status === 'SUCCESS') {
            toast.success('Analysis completed!');
          } else if (payload.new.status === 'FAILED') {
            toast.error(`Analysis failed: ${payload.new.result_message}`);
          }
        }
      )
      .subscribe();
    
    return () => {
      supabase.removeChannel(channel);
    };
  }, [jobId]);
  
  return { status, message };
}
```

### Complete Example

```typescript
// Complete integration example
export async function analyzeDocument(sourceId: string, userId: string) {
  // Step 1: Create job
  const jobId = await triggerAnalysis(sourceId, userId);
  
  // Step 2: Trigger GitHub Actions
  await triggerGitHubWorkflow(sourceId, jobId);
  
  // Step 3: Return jobId for UI to track
  return jobId;
}

// In your component
function AnalysisButton({ sourceId }: { sourceId: string }) {
  const [jobId, setJobId] = useState<string | null>(null);
  const { status, message } = useJobStatus(jobId);
  
  const handleAnalyze = async () => {
    const newJobId = await analyzeDocument(sourceId, user.id);
    setJobId(newJobId);
  };
  
  return (
    <div>
      <button onClick={handleAnalyze}>Start Analysis</button>
      {jobId && (
        <div>
          Status: {status}
          {message && <p>{message}</p>}
        </div>
      )}
    </div>
  );
}
```

---

## 🔐 Required GitHub Secrets

The workflow requires the following secrets to be configured in your GitHub repository:

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `SUPABASE_URL` | Your Supabase project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (admin access) | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Anonymous key | Supabase Dashboard → Settings → API |
| `GEMINI_API_KEY` | Google Gemini API key | Google AI Studio |

### Setting Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its corresponding value

---

## 📊 Workflow Execution Flow

### Complete Pipeline (`v40-complete`)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Environment Validation                                  │
│     - Check all required secrets                            │
│     - Verify Python dependencies                            │
│     - Validate source_id format                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Stage 1: Enhanced Extraction (v40-extract)              │
│     - Read source translations from database                │
│     - Extract metadata with constitutional detection        │
│     - Parse preamble and articles                           │
│     - Save to source_ai_analysis table                      │
│     Status Update: "Stage 1 completed"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Stage 2: Definitive Analysis (v40-analyze)              │
│     - Analyze each article with V4.2 prompts                │
│     - Extract entities, tags, and relationships             │
│     - Generate bilingual summaries                          │
│     - Save analysis results                                 │
│     Status Update: "Stage 2 completed"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Stage 3: Final Synthesis (v40-synthesize)               │
│     - Generate law-level summary                            │
│     - Suggest document category                             │
│     - Synthesize all article analyses                       │
│     Status Update: "Stage 3 completed"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Stage 4: Law Ingestion (v40-ingest)                     │
│     - Create law record with correct metadata               │
│     - Create article versions                               │
│     - Build knowledge graph with relationships              │
│     - Generate final translations                           │
│     Status Update: "SUCCESS - Analysis completed"           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6. Job Status Update (if job_id provided)                  │
│     - Update background_jobs.status = 'SUCCESS'             │
│     - Set result_message with details                       │
│     - Trigger real-time notification to user                │
└─────────────────────────────────────────────────────────────┘
```

### Error Handling

If any stage fails:
1. Workflow captures error message
2. If `job_id` is provided:
   - Updates `background_jobs.status = 'FAILED'`
   - Sets `result_message` with error details
   - Triggers real-time notification
3. Workflow exits with failure status

---

## 🎯 Usage Examples

### Example 1: Standard Analysis (No Job Tracking)

**Trigger manually from GitHub Actions UI:**

```yaml
Inputs:
  source_id: "d7eaa191-fd7b-48ef-9013-33579398d6ad"
  pipeline_stage: "v40-complete"
  job_id: (leave empty)
```

**No real-time tracking, but analysis completes successfully.**

### Example 2: With Job Tracking (Recommended for App)

**From Next.js:**

```typescript
const jobId = await createBackgroundJob('KRITIS_V40_ANALYSIS', { source_id: sourceId });

await triggerGitHubWorkflow({
  source_id: sourceId,
  job_id: jobId, // ⭐ Enable tracking
  pipeline_stage: 'v40-complete'
});

// User gets real-time updates via Supabase Realtime
```

### Example 3: Constitutional Document

```typescript
// Same as Example 2, but the enhanced system will:
// - Detect it's a constitutional document
// - Use source translations for proper title
// - Set official_number to "CRP"
// - Set law_type_id to "CONSTITUTION"
// - Set enactment_date to "1976-04-02"
// - Generate proper slug: "crp-19760402"

await analyzeDocument("d7eaa191-fd7b-48ef-9013-33579398d6ad", userId);
```

### Example 4: Rerun Single Stage

If synthesis failed, rerun just that stage:

```yaml
Inputs:
  source_id: "d7eaa191-fd7b-48ef-9013-33579398d6ad"
  pipeline_stage: "v40-synthesize"
  job_id: "550e8400-e29b-41d4-a716-446655440000"
```

---

## 📈 Monitoring & Debugging

### Check Workflow Execution

1. Go to your GitHub repository
2. Click **Actions** tab
3. Find your workflow run
4. View logs and summary

### Database Queries

Check job status:
```sql
SELECT id, job_type, status, result_message, created_at, updated_at
FROM agora.background_jobs
WHERE id = 'your-job-id';
```

Check analysis results:
```sql
SELECT model_version, analysis_data
FROM agora.source_ai_analysis
WHERE source_id = 'your-source-id'
ORDER BY created_at DESC;
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid UUID format | source_id not a valid UUID | Verify UUID format |
| Missing secrets | GitHub secrets not configured | Add all 4 required secrets |
| Job status not updating | job_id not provided or invalid | Pass valid job_id from create_new_job() |
| Analysis fails on constitution | Old version of code | Ensure using commit fc0734a or later |

---

## 🔄 Version History

| Version | Commit | Date | Changes |
|---------|--------|------|---------|
| 1.0 | fc0734a | 2025-10-04 | Added job_id support, constitutional fix |
| 0.9 | 92bf4f8 | 2025-10-04 | Added background job notification system |
| 0.8 | (earlier) | 2025-10-03 | Initial V4.0 PROD10 workflow |

---

## 📚 Additional Resources

- **Test Reports**: See `context/TEST_REPORT_METADATA_EXTRACTION.md`
- **Constitutional Fix Details**: See `context/CONSTITUTIONAL_DOCUMENT_FIX.md`
- **Session Summary**: See `context/SESSION_SUMMARY_2025_10_04.md`
- **Main Pipeline**: See `agora-analyst-python/main.py`
- **Analyzer Code**: See `agora-analyst-python/analysis/kritis_analyzer_v4.py`

---

## 🎯 Quick Start Checklist

- [ ] Configure all 4 GitHub secrets
- [ ] Implement `create_new_job()` function in Next.js
- [ ] Set up Octokit with GitHub token
- [ ] Implement Supabase Realtime listener
- [ ] Test with a sample document
- [ ] Monitor job status in database
- [ ] Add error handling and user notifications

---

**Last Updated**: 2025-10-04  
**Maintained By**: Agora Analyst Team  
**Status**: ✅ Production Ready
