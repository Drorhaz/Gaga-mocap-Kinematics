# Should We Remove Offsets from Schema?

## Recommendation: **Keep Them, But Mark as Reference Only**

### Why Keep Them:

1. **Documentation/Reference**: 
   - They document what the original BVH file contained
   - Useful for understanding the skeleton model structure
   - Part of the BVH standard format

2. **Future Flexibility**:
   - If you implement per-session offset extraction later, the structure is already there
   - Can enable BVH comparison with `use_bvh_offsets=True` if per-session offsets are available

3. **No Harm**:
   - They're not used by default anymore (`use_bvh_offsets=False`)
   - Code safely ignores them if not enabled
   - Small file size impact

### Why NOT Remove Them:

1. **Loses Reference Data**: 
   - Removes documentation of the original BVH structure
   - Makes it harder to understand the skeleton model

2. **Breaks BVH Standard**:
   - Offsets are part of the BVH format specification
   - Removing them makes the schema less complete

3. **Future Use**:
   - If you later want per-session offsets, you'd need to add the structure back

---

## What I Did

### ✅ Added Documentation Note

Updated `skeleton_schema.json` to add a note in the `notes` section:

```json
"notes": {
  "quat_convention": "xyzw (SciPy Rotation format)",
  "intended_use": "schema + bone-length QC + joint hierarchy for q_local",
  "offsets_note": "Offsets are session-specific (from BVH file). Not used by default in QC (use_bvh_offsets=False). Keep for reference/documentation only. For multi-subject data, QC uses consistency check (CV%) instead of BVH comparison."
}
```

This clarifies:
- Offsets are session-specific
- Not used by default
- Kept for reference only
- QC uses consistency check instead

---

## Alternative: Remove Completely

If you want to remove them entirely:

**Pros:**
- ✅ Cleaner schema (no misleading session-specific data)
- ✅ Smaller file size
- ✅ Clearer that schema is generic

**Cons:**
- ❌ Loses reference documentation
- ❌ Would need to add structure back if implementing per-session offsets later
- ❌ Less complete BVH representation

---

## My Recommendation

**Keep offsets in schema** but:
1. ✅ **Documented as reference only** (done)
2. ✅ **Not used by default** (done in qc.py)
3. ✅ **Optional if needed** (can enable with `use_bvh_offsets=True`)

This gives you:
- Reference documentation
- Flexibility for future per-session implementation
- No false warnings (disabled by default)
- Clean separation (offsets exist but aren't used)

---

## Summary

**Current State:**
- Offsets in schema ✅ (kept for reference)
- Not used by default ✅ (use_bvh_offsets=False)
- Documented as reference only ✅ (added note)

**This is optimal** - you get the benefits without the problems!
