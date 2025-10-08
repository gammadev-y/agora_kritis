# Law Type Fix - Production Deployment Guide

## Overview

This update fixes the foreign key constraint violation error when inserting laws with invalid `type_id` values. The fix ensures all law types are correctly mapped to valid database IDs from the `law_types` table.

## What Changed

### 1. Enhanced Law Type Mapping
- **File:** `agora-analyst-python/analysis/kritis_analyzer_v50.py`
- **Method:** `_map_law_type()`
- **Lines:** ~470-590

**Improvements:**
- Now supports all 68 law types from database
- Case-insensitive matching
- Automatic fallback to 'OTHER' for unknown types
- No database calls (static mapping)

### 2. Better Metadata Extraction
- Enhanced regex patterns to recognize more Portuguese legal document types
- More accurate type identification from source documents

## Deployment Steps

### 1. Backup Current Version (Optional but Recommended)
```bash
cd /home/gamma/Documents/Agora_Analyst/agora-analyst-python
cp analysis/kritis_analyzer_v50.py analysis/kritis_analyzer_v50.py.backup
```

### 2. Verify Changes
```bash
# The updated file should already be in place
# Verify the _map_law_type method exists and is comprehensive
grep -A 5 "def _map_law_type" analysis/kritis_analyzer_v50.py
```

### 3. Run Validation Test
```bash
cd /home/gamma/Documents/Agora_Analyst/agora-analyst-python
python3 test_law_type_mapping.py
```

**Expected output:**
```
✅ All tests passed! All law type mappings are valid.
```

### 4. Test with Real Document (Recommended)
Process a test document through the workflow to ensure:
- Law type is correctly identified
- No foreign key constraint violations
- Law record is created successfully

### 5. Monitor Logs
After deployment, monitor for these log messages:
- `⚠️ Unknown law type '<type>', defaulting to OTHER` - indicates a new/unrecognized type
- `📋 Extracted official_number from content: <number>` - confirms successful extraction

## Rollback Procedure

If issues occur, restore the backup:
```bash
cd /home/gamma/Documents/Agora_Analyst/agora-analyst-python
cp analysis/kritis_analyzer_v50.py.backup analysis/kritis_analyzer_v50.py
```

## Verification Checklist

Before marking as complete:
- [ ] Test script passes all validations
- [ ] At least one real document processes successfully
- [ ] No foreign key constraint violations in logs
- [ ] Law records created with valid type_id
- [ ] Unknown types gracefully fallback to 'OTHER'

## Common Issues & Solutions

### Issue: "Unknown law type X, defaulting to OTHER"
**Cause:** Document has a type not in our mapping  
**Solution:** 
1. Check if it's a valid type in `law_types` table
2. If valid, add to mapping in `_map_law_type()`
3. If new type, add to database first, then update mapping

### Issue: Still getting constraint violations
**Cause:** Type mapped to ID that doesn't exist in `law_types`  
**Solution:**
1. Check error message for the invalid type_id
2. Verify type exists: `SELECT id FROM law_types WHERE id = '<type_id>';`
3. If missing, either add to database or fix mapping

### Issue: Type extracted incorrectly from document
**Cause:** Regex pattern not matching document format  
**Solution:**
1. Check document format
2. Update regex in `_extract_metadata()` if needed
3. Ensure Kritis prompt can identify type from content

## Monitoring Recommendations

Monitor these metrics post-deployment:
1. **Foreign key violations:** Should drop to zero
2. **'OTHER' type usage:** Should be minimal (indicates unknown types)
3. **Successful law insertions:** Should increase
4. **Warning logs:** Review for new document types to add

## Files Reference

| File | Purpose |
|------|---------|
| `kritis_analyzer_v50.py` | Main implementation with fixed mapping |
| `test_law_type_mapping.py` | Validation test suite |
| `LAW_TYPE_FIX_SUMMARY.md` | Detailed implementation summary |
| `LAW_TYPE_REFERENCE.md` | Quick reference for all law types |

## Support

If issues persist:
1. Check logs for specific error messages
2. Verify database `law_types` table has all expected types
3. Run validation test to ensure mapping is correct
4. Review document content to see what type is being extracted

## Success Criteria

Deployment is successful when:
- ✅ No foreign key constraint violations
- ✅ All common Portuguese law types recognized
- ✅ Unknown types gracefully handled with 'OTHER'
- ✅ Workflow completes without errors
- ✅ Law records created with correct type_id

---

**Last Updated:** 2025-10-08  
**Version:** v50 (Kritis V5.0)
