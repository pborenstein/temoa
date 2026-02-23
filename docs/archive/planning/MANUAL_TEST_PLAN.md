# Manual Test Plan - Obsidian Filter Syntax

## Test Environment

- URL: http://localhost:8080
- View: Explorer view (right pane)
- Test vault: amoxtli (or any configured vault)

## Basic Filter Tests

### 1. Single Tag Filter
**Input:** `tag:python`
**Expected:** Only results with #python tag

### 2. Path Filter
**Input:** `path:Gleanings`
**Expected:** Only results with "Gleanings" in path

### 3. File Filter
**Input:** `file:README`
**Expected:** Only results with "README" in filename

### 4. Property Syntax - Type
**Input:** `[type:gleaning]`
**Expected:** Only gleanings (type=gleaning in frontmatter)

### 5. Property Syntax - Status
**Input:** `[status:active]`
**Expected:** Only active status documents

## Boolean Operator Tests

### 6. Explicit OR
**Input:** `tag:python OR tag:javascript`
**Expected:** Results with EITHER python OR javascript tag

### 7. Implicit AND (space)
**Input:** `tag:ai path:research`
**Expected:** Results with BOTH ai tag AND "research" in path

### 8. Negation
**Input:** `-tag:draft`
**Expected:** Results WITHOUT draft tag

### 9. Grouped OR with AND
**Input:** `(tag:ai OR tag:ml) path:research`
**Expected:** Results with (ai OR ml) tag AND "research" in path

## Quoted Values Tests

### 10. Path with Spaces
**Input:** `path:"Daily notes"`
**Expected:** Results with "Daily notes" in path (exact phrase)

### 11. Filename with Spaces
**Input:** `file:"My Document"`
**Expected:** Results with "My Document" in filename

## Backward Compatibility Tests

### 12. Comma Syntax (ANY mode)
**Input:** `tag:python,javascript`
**Expected:** Results with python OR javascript tag (converted to OR)

### 13. Multiple Commas
**Input:** `tag:python,javascript,rust`
**Expected:** Results with python OR javascript OR rust tag

## Complex Queries

### 14. User's Example
**Input:** `[type:gleaning] -[type:daily]`
**Expected:** Gleanings but NOT daily notes

### 15. Complex Boolean
**Input:** `(tag:python OR tag:rust) path:L/Gleanings -tag:wip`
**Expected:** Results with (python OR rust) tag AND "L/Gleanings" in path AND NOT wip tag

### 16. Mixed Filters
**Input:** `tag:ai [type:gleaning] path:research -tag:draft`
**Expected:** Gleanings with ai tag AND "research" in path AND NOT draft tag

## Error Handling Tests

### 17. Missing Right Operand
**Input:** `tag:python OR`
**Expected:** Parse error message (user-friendly)

### 18. Unmatched Parenthesis
**Input:** `(tag:python`
**Expected:** Parse error message

### 19. Unmatched Bracket
**Input:** `[type:gleaning`
**Expected:** Parse error message

### 20. Missing Value
**Input:** `tag:`
**Expected:** Parse error message

## UI/UX Tests

### 21. Help Panel
**Action:** Click the "?" button next to filter input
**Expected:** Help panel shows Obsidian syntax examples

### 22. Filter Chip Display
**Action:** Enter filter: `tag:python OR tag:javascript`
**Expected:** Single chip shows the full filter text

### 23. State Persistence
**Action:**
1. Set filter: `tag:python OR tag:javascript`
2. Refresh page (F5)
**Expected:** Filter persists and results still filtered

### 24. Migration from Old State
**Action:**
1. Clear localStorage: `localStorage.clear()` in console
2. Manually set old state:
```javascript
localStorage.setItem('temoa-explorer-state', JSON.stringify({
  filterParams: {
    filterText: 'tag:python,javascript',
    tagMatchMode: 'any'
  }
}))
```
3. Refresh page
**Expected:** Filter migrated to `tag:python OR tag:javascript`

## Performance Tests

### 25. Parser Performance
**Action:** In browser console:
```javascript
console.time('parse')
const lexer = new FilterLexer('(tag:python OR tag:javascript) path:research -tag:draft')
const tokens = lexer.tokenize()
const parser = new FilterParser(tokens)
const ast = parser.parse()
console.timeEnd('parse')
```
**Expected:** < 2ms

### 26. Evaluation Performance
**Action:** In browser console (after search):
```javascript
console.time('eval')
const filtered = state.rawResults.filter(r => evaluateAST(state.filterParams.ast, r, ''))
console.timeEnd('eval')
```
**Expected:** < 10ms for 100 results

### 27. Total Filter Time
**Action:** Enter complex filter, observe response time
**Expected:** < 100ms for filtering

## Regression Tests

### 28. No ANY/ALL Toggle
**Expected:** Toggle should be removed from UI

### 29. Search Still Works
**Action:** Regular search without filters: `python`
**Expected:** Search results appear normally

### 30. View Switching
**Action:** Switch between List and Explorer views
**Expected:** Filters persist and work in both views

## Success Criteria

- [ ] All 30 tests pass
- [ ] No JavaScript console errors
- [ ] Filter syntax matches Obsidian behavior
- [ ] Performance meets targets (<2ms parse, <10ms eval, <100ms total)
- [ ] State migration works for existing users
- [ ] Help panel accurate and helpful
- [ ] No regression in core search functionality
