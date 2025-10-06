# Dynamic Workflow System

This document explains how the Agora Analyst dynamic workflow system works and how to integrate it with external applications.

## Overview

The Agora Analyst Python service exposes a **workflow manifest** that describes all available analysis workflows. This manifest is automatically published to GitHub Pages whenever changes are pushed to the master branch.

## Workflow Manifest Structure

The manifest is a JSON array of workflow objects. Each workflow has the following structure:

```json
{
  "id": "v50-complete",
  "name": "Kritis V5.0 - Complete Pipeline (Enhanced Relationships)",
  "description": "Runs the complete V5.0 pipeline with enhanced relationship processing...",
  "stages": ["extract", "analyze", "build-graph"],
  "version": "5.0",
  "status": "stable",
  "recommended": true,
  "features": [
    "URL-based reference matching",
    "Law-to-law relationships",
    "Article-to-article relationships"
  ]
}
```

### Field Descriptions

- **id**: Unique workflow identifier (used in CLI commands)
- **name**: Human-readable workflow name
- **description**: Detailed description of what the workflow does
- **stages**: Array of pipeline stages included in this workflow
- **version**: Workflow version number
- **status**: Current workflow status (`stable`, `beta`, `deprecated`)
- **recommended**: Boolean indicating if this is the recommended workflow for new documents
- **features** (optional): Array of key features for this workflow

## Accessing the Manifest

### Local Development

Generate the manifest locally:

```bash
cd agora-analyst-python
python main.py describe-workflows > workflow-manifest.json
```

### Production (GitHub Pages)

Once the GitHub Action runs, the manifest will be available at:

```
https://<username>.github.io/<repo-name>/workflow-manifest.json
```

For this repository:
```
https://gammadev-y.github.io/agora_kritis/workflow-manifest.json
```

## Integration Example (Next.js/TypeScript)

### 1. Fetch Workflows on Application Load

```typescript
// lib/workflows.ts
interface Workflow {
  id: string;
  name: string;
  description: string;
  stages: string[];
  version: string;
  status: 'stable' | 'beta' | 'deprecated';
  recommended: boolean;
  features?: string[];
}

export async function fetchWorkflows(): Promise<Workflow[]> {
  const response = await fetch(
    'https://gammadev-y.github.io/agora_kritis/workflow-manifest.json'
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch workflow manifest');
  }
  
  return response.json();
}
```

### 2. Display in UI

```typescript
// components/WorkflowSelector.tsx
import { useEffect, useState } from 'react';
import { fetchWorkflows } from '@/lib/workflows';

export function WorkflowSelector() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  
  useEffect(() => {
    fetchWorkflows().then(workflows => {
      setWorkflows(workflows);
      // Auto-select recommended workflow
      const recommended = workflows.find(w => w.recommended);
      if (recommended) {
        setSelectedId(recommended.id);
      }
    });
  }, []);
  
  return (
    <select value={selectedId} onChange={e => setSelectedId(e.target.value)}>
      {workflows.map(workflow => (
        <option key={workflow.id} value={workflow.id}>
          {workflow.name} {workflow.recommended && '(Recommended)'}
        </option>
      ))}
    </select>
  );
}
```

### 3. Execute Analysis with Selected Workflow

```typescript
// app/actions/analyze.ts
'use server';

export async function analyzeDocument(
  sourceId: string,
  workflowId: string
) {
  // Call your Python service with the selected workflow
  const response = await fetch('http://your-python-service/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_id: sourceId,
      workflow_id: workflowId
    })
  });
  
  return response.json();
}
```

## Benefits

1. **No Hardcoding**: Frontend doesn't need to hardcode workflow options
2. **Automatic Updates**: New workflows appear automatically when manifest updates
3. **Self-Documenting**: Workflows include descriptions and feature lists
4. **Version Management**: Easy to deprecate old workflows and introduce new ones
5. **Recommended Workflows**: System can guide users to the best workflow

## CI/CD Pipeline

The workflow manifest is automatically updated via GitHub Actions:

1. Developer pushes changes to `master` branch
2. GitHub Action triggers
3. Action runs `python main.py describe-workflows`
4. Generated manifest is published to GitHub Pages
5. Frontend applications fetch updated manifest

## Adding New Workflows

To add a new workflow:

1. Implement the workflow in `analysis/kritis_analyzer_vXX.py`
2. Add CLI command handlers in `main.py`
3. Add workflow description to the manifest in `main.py` (in the `describe-workflows` command handler)
4. Push to master - GitHub Actions handles the rest!

## Workflow Status Lifecycle

- **beta**: New workflow in testing
- **stable**: Production-ready workflow
- **deprecated**: Old workflow, will be removed in future version

## Current Available Workflows

Run `python main.py describe-workflows` to see all current workflows, or check the published manifest at GitHub Pages.
