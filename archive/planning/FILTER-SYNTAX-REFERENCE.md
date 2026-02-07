# Temoa Filter Syntax Reference

**Quick reference for Obsidian-style filtering in Temoa Explorer view**

**Full Obsidian Syntax**: [https://help.obsidian.md/plugins/search](https://help.obsidian.md/plugins/search)

**Note**: Temoa implements a subset of Obsidian's search operators.

---

## Basic Syntax

```
tag:value          Filter by tag
path:value         Filter by path substring
file:value         Filter by filename substring
type:value         Filter by type (server-side)
status:value       Filter by status (server-side)
```

---

## Examples

### Single Tag
```
tag:python
```
Shows only documents tagged with `python`.

---

### Multiple Tags (OR)
```
tag:python,obsidian
```
Shows documents with `python` OR `obsidian` tag.

Toggle: Set to **ANY** mode.

---

### Multiple Tags (AND)
```
tag:python,obsidian
```
Shows documents with `python` AND `obsidian` tags.

Toggle: Set to **ALL** mode.

---

### Path Filtering
```
path:L/Gleanings
```
Shows documents with `L/Gleanings` in their path.

Case-insensitive.

---

### Filename Filtering
```
file:README
```
Shows documents with `README` in their filename.

Case-insensitive.

---

### Combined Filters
```
semantic search tag:python path:L/Gleanings
```

- **Query**: "semantic search" (sent to server)
- **Filters**: Applied client-side after results return

Filters are AND-ed together (must match all).

---

## Tag Match Modes

### ANY Mode (Default)
Results need **at least one** of the specified tags.

Example: `tag:python,javascript` → docs with python OR javascript

---

### ALL Mode
Results need **all** of the specified tags.

Example: `tag:python,javascript` → docs with python AND javascript

Toggle between modes using ANY/ALL buttons.

---

## Advanced Examples

### Complex Query
```
vault research tag:ai,ml path:Papers file:transformer
```

Matches documents that:
- Match semantic query "vault research"
- Have tag `ai` OR `ml` (if ANY mode)
- Have `Papers` in path
- Have `transformer` in filename

---

### Empty Filter
```
(empty input)
```
Shows all results (no filtering).

---

## Tips

1. **Instant Feedback**: All tag/path/file filters apply instantly (no server round-trip)

2. **Case-Insensitive**: Path and file filters ignore case

3. **Fail-Open**: Documents missing frontmatter fields are excluded from tag filters

4. **Remove Filters**: Click × on filter chips to remove specific filters

5. **Persistence**: Filter state saves across page reloads

6. **Help Panel**: Click ? button for in-app help

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Type in filter input | Auto-update filters |
| Click chip × | Remove specific filter |
| Click ANY/ALL | Toggle tag match mode |
| Click ? | Toggle help panel |

---

## Coming Soon (Phase 2+)

### Property Filtering
```
[project]:temoa
[status]:active
[author]:pborenstein
```

### Date Filtering
```
created:>2025-01-01
modified:<30d
```

---

## Performance

- **Filter parsing**: < 5ms
- **50 results, 5 filters**: < 50ms
- **100 results, 10 filters**: < 100ms
- **No network overhead**: Pure client-side

---

## Filter Chips

Active filters appear as blue chips below the input:

```
┌──────────────────────────────────────┐
│ tag:python path:L/Gleanings file:README │
├──────────────────────────────────────┤
│ ┌──────────┐ ┌─────────────────┐   │
│ │ tag:python ×│ │ path:L/Gleanings ×│   │
│ └──────────┘ └─────────────────┘   │
│ ┌─────────────┐                    │
│ │ file:README ×│                    │
│ └─────────────┘                    │
└──────────────────────────────────────┘
```

Click × to remove individual filters.

---

## Troubleshooting

### No Results After Filtering
- Check if filter is too restrictive
- Verify documents have the specified tags/paths
- Try removing filters one at a time

### Filter Not Working
- Check for typos in filter syntax
- Ensure proper spacing (e.g., `tag:python` not `tag: python`)
- Check browser console for errors

### Chips Not Appearing
- Filter input may be empty
- Check if valid filter syntax was used
- Try toggling help panel (?) to verify syntax

---

## Related Documentation

- **Implementation Details**: See `PHASE1-IMPLEMENTATION-SUMMARY.md`
- **Testing Guide**: See `FILTER-TESTING-GUIDE.md`
- **Architecture**: See `docs/SEARCH-MECHANISMS.md`

---

**Version**: Phase 1 (v0.7.0)
**Last Updated**: 2026-02-01
