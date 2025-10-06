# Quick Reference Card - Dynamic Workflow System

## 🚀 For Developers

### Generate Manifest Locally
```bash
cd agora-analyst-python
python main.py describe-workflows > workflow-manifest.json
```

### Test Analysis with Specific Workflow
```bash
python main.py --source-id <UUID> v50-complete
python main.py --source-id <UUID> v40-complete
```

### List All Available Workflows
```bash
python main.py describe-workflows | jq '.[].id'
```

### Find Recommended Workflow
```bash
python main.py describe-workflows | jq '.[] | select(.recommended==true) | .id'
# Output: "v50-complete"
```

---

## 🌐 For Frontend Integration

### Fetch Manifest (Production)
```typescript
const response = await fetch(
  'https://gammadev-y.github.io/agora_kritis/workflow-manifest.json'
);
const workflows = await response.json();
```

### Get Recommended Workflow
```typescript
const recommended = workflows.find(w => w.recommended);
console.log(recommended.id); // "v50-complete"
```

### Filter by Version
```typescript
const v5Workflows = workflows.filter(w => w.version === "5.0");
```

### Filter by Status
```typescript
const stableWorkflows = workflows.filter(w => w.status === "stable");
```

---

## 📊 Workflow IDs Quick Reference

### V4.0 (PROD10)
- `v40-complete` - Full pipeline (4 stages)
- `v40-extract` - Extraction only
- `v40-analyze` - Analysis only
- `v40-synthesize` - Synthesis only
- `v40-ingest` - Ingestion only

### V5.0 (Enhanced Relationships) ⭐
- `v50-complete` - Full pipeline (3 stages) ✅ **RECOMMENDED**
- `v50-extract` - Extraction only
- `v50-analyze` - Analysis only
- `v50-build-graph` - Knowledge graph only

---

## 🔧 GitHub Pages Setup

1. **Enable GitHub Pages**
   - Repository Settings → Pages
   - Source: `gh-pages` branch
   - Root directory

2. **Trigger Workflow**
   - Push to `master` branch, OR
   - Actions tab → "Publish Workflow Manifest" → Run workflow

3. **Verify Deployment**
   ```bash
   curl https://gammadev-y.github.io/agora_kritis/workflow-manifest.json
   ```

---

## 🐛 Troubleshooting

### Manifest Not Updating
```bash
# Check GitHub Actions status
# Go to: https://github.com/gammadev-y/agora_kritis/actions

# Manually trigger workflow
# Actions tab → "Publish Workflow Manifest" → Run workflow
```

### Invalid JSON Error
```bash
# Validate locally
python main.py describe-workflows | python -m json.tool
```

### 404 on GitHub Pages
```bash
# Check if gh-pages branch exists
git branch -r | grep gh-pages

# Verify GitHub Pages is enabled in Settings
```

---

## 📝 Adding New Workflow

1. **Implement in Python**
   ```python
   # analysis/kritis_analyzer_v60.py
   class KritisAnalyzerV60:
       # ... implementation
   ```

2. **Add CLI Command**
   ```python
   # main.py
   subparsers.add_parser('v60-complete', help='...')
   ```

3. **Add to Manifest**
   ```python
   # main.py (in describe-workflows handler)
   workflows.append({
       "id": "v60-complete",
       "name": "Kritis V6.0 - New Features",
       "description": "...",
       "stages": ["extract", "analyze", "transform"],
       "version": "6.0",
       "status": "beta",
       "recommended": False
   })
   ```

4. **Push to Master**
   ```bash
   git add .
   git commit -m "feat: add v60 workflow"
   git push origin master
   # GitHub Actions will auto-publish updated manifest
   ```

---

## 🎯 Common Use Cases

### Default Workflow for New Documents
```typescript
const workflows = await fetchWorkflows();
const defaultWorkflow = workflows.find(w => w.recommended);
// Use: defaultWorkflow.id
```

### Show Only Stable Workflows
```typescript
const stable = workflows.filter(w => w.status === 'stable');
```

### Display Features to User
```typescript
const workflow = workflows.find(w => w.id === 'v50-complete');
console.log('Features:', workflow.features);
// Output: ["URL-based reference matching", "Law-to-law relationships", ...]
```

### Deprecation Warning
```typescript
if (workflow.status === 'deprecated') {
  alert(`Warning: ${workflow.name} is deprecated. Please use a recommended workflow.`);
}
```

---

## ✅ Verification Commands

```bash
# Count workflows
python main.py describe-workflows | jq 'length'
# Expected: 9

# Check recommended
python main.py describe-workflows | jq '[.[] | select(.recommended==true)] | length'
# Expected: 1

# Validate all workflows have required fields
python main.py describe-workflows | jq '.[] | {id, name, version, status}'
```

---

## 📦 Manifest Schema

```typescript
interface Workflow {
  id: string;                    // Required: Unique identifier
  name: string;                  // Required: Display name
  description: string;           // Required: Full description
  stages: string[];              // Required: Pipeline stages
  version: string;               // Required: Version number
  status: 'stable' | 'beta' | 'deprecated'; // Required
  recommended: boolean;          // Required: Is this the recommended workflow?
  features?: string[];           // Optional: Array of feature descriptions
}

type WorkflowManifest = Workflow[];
```

---

## 🔗 Useful Links

- **GitHub Pages URL**: https://gammadev-y.github.io/agora_kritis/workflow-manifest.json
- **GitHub Actions**: https://github.com/gammadev-y/agora_kritis/actions
- **Full Documentation**: See `DYNAMIC_WORKFLOW_SYSTEM.md`
- **Implementation Summary**: See `IMPLEMENTATION_SUMMARY_V50_DYNAMIC.md`
