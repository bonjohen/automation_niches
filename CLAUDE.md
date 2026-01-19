When facing architectural or implementation choices, Claude should:
1. **Choose the best option** based on project constraints (simplicity, determinism, restart-safety)
2. **Document the decision** in `docs/project/todo.md` under "Resolved Decisions"
3. **Explain the rationale** briefly when making the choice
4. **Prefer:** simplicity over cleverness, determinism over parallelism, file-based over networked

## Agent Operating Rules

1. Make architectural decisions autonomously when needed; document rationale in todo.md.
2. Prefer `/delegate` for scoped, non-authoritative processing or evaluation tasks.
3. When information stabilizes, persist it in files and treat prior discussion as disposable.
4. File placement rules:
   - Temporary files: `/tmp/a_story_night/`
   - Logs: `/log/<producer>/`
   - Source data: `/data/<source>/`
   - Executables: appropriate `bin/` directories
   - Avoid files in root unless they truly belong there
   - Discover and respect existing structure before creating new paths
5. Minimize change scope; prefer localized modifications over broad rewrites unless explicitly directed.

## Invariants

- **Never delete user data**; only move or rename
- **All state transitions must be logged**
- **Processing must be idempotent and restart-safe**
- **Completed outputs must never be silently overwritten**
- **Recovery logic always runs before new work is claimed**

## File Safety

- Treat all filesystem operations as potentially fallible
- Prefer atomic moves and renames
- Assume the system may crash or restart at any point
- Use write-to-temp-then-rename pattern for all writes

## Behavior

- As progress is made, update project documentation (`todo.md`, etc.)
- Immediately before a commit, clean up folders that may have misplaced files
- Favor simple, deterministic designs over clever optimizations
- Make recovery paths explicit and testable
- Keep job state externalized to files, not memory
- Avoid introducing databases or network dependencies unless explicitly required