# Ralph Workflow Guide

## Core Loop

Ralph executes this cycle until all stories pass or max iterations reached:

1. **Branch Management** - Create/checkout feature branch from prd.json
2. **Story Selection** - Find highest-priority story where `passes: false`
3. **Implementation** - AI agent implements the story
4. **Quality Gates** - Run typecheck and tests
5. **Commit & Update** - On success, commit and mark `passes: true`
6. **Learning Capture** - Append insights to progress.txt
7. **Iteration** - Spawn fresh AI instance for next story

## Starting a Ralph Run

### 1. Create PRD

Create `prd.json` in your project root:

```json
{
  "branchName": "ralph/my-feature",
  "userStories": [
    {
      "id": 1,
      "title": "Add user profile schema with name and email",
      "passes": false
    },
    {
      "id": 2,
      "title": "Create profile edit form component",
      "passes": false
    }
  ]
}
```

### 2. Launch Ralph

```bash
# Default (Amp, 10 iterations)
./scripts/ralph/ralph.sh

# Claude Code, 20 iterations
./scripts/ralph/ralph.sh --tool claude 20

# Custom iteration count
./scripts/ralph/ralph.sh 15
```

### 3. Monitor Progress

Ralph displays each iteration's output in real-time. Watch for:
- Story implementation details
- Quality gate results (typecheck, tests)
- Completion signal: `<promise>COMPLETE</promise>`

## During Execution

### What Ralph Does Each Iteration

1. **Reads prd.json** - Identifies next incomplete story
2. **Reads progress.txt** - Loads learnings from previous iterations
3. **Reads AGENTS.md** - Incorporates codebase conventions
4. **Implements story** - Writes code to complete the user story
5. **Runs quality gates** - Executes typecheck and tests
6. **On success:**
   - Commits changes with descriptive message
   - Updates story `passes: true` in prd.json
   - Appends learnings to progress.txt
7. **On failure:**
   - Records issue in progress.txt
   - Attempts fix in next iteration

### File Updates During Run

- **prd.json** - `passes` flags update as stories complete
- **progress.txt** - Append-only log grows with learnings
- **AGENTS.md** - Updated with discovered patterns and gotchas
- **Git history** - Each successful story gets a commit

## Monitoring Status

### Check completion status
```bash
cat prd.json | jq '.userStories[] | {id, title, passes}'
```

### View recent learnings
```bash
tail -20 progress.txt
```

### Check iteration commits
```bash
git log --oneline -10
```

### Count remaining stories
```bash
cat prd.json | jq '[.userStories[] | select(.passes == false)] | length'
```

## Completion

Ralph exits when either:

1. **Success** - All stories have `passes: true`
   - Outputs: `<promise>COMPLETE</promise>`
   - Feature branch ready for review

2. **Max iterations** - Iteration limit reached
   - Check prd.json for remaining stories
   - Review progress.txt for issues
   - Can resume by running ralph again

## Archiving

When you change `branchName` in prd.json, Ralph automatically archives the previous run:

```
archive/
  └── 2024-03-15-previous-feature/
      ├── prd.json
      └── progress.txt
```

This preserves history when starting new features.

## Best Practices

### 1. Right-Size Stories
Each story should fit in one context window:
- ✓ "Add user profile database schema"
- ✗ "Build complete authentication system"

### 2. Maintain Quality Gates
Broken tests compound across iterations. Ensure:
- Tests run successfully before starting
- Typecheck passes
- CI remains green

### 3. Review AGENTS.md
Check updates after runs to understand what Ralph learned about your codebase.

### 4. Monitor progress.txt
Early iterations reveal patterns in failures. Address systemic issues (missing dependencies, incorrect paths) before they repeat.

### 5. Verify UI Changes
For frontend stories, use browser verification:
- Include browser screenshots in commits
- Verify visual correctness, not just tests
- Use dev-browser skill if available

## Troubleshooting

### Ralph keeps failing the same story
1. Check progress.txt for error patterns
2. Verify quality gates work manually
3. Consider splitting story into smaller pieces
4. Update AGENTS.md with missing context

### Tests pass but story marked failed
Check prompt template's quality gate commands match your project's test commands.

### Branch not created
Ensure git repo is initialized and prd.json has valid branchName field.

### Quality gates timeout
Adjust iteration count or optimize test suite. Ralph needs fast feedback loops.

## Resuming After Pause

Ralph is stateless - all context in files:

```bash
# Resume any time
./scripts/ralph/ralph.sh

# Ralph reads:
# - prd.json (current state)
# - progress.txt (learnings)
# - AGENTS.md (conventions)
# - git history (previous work)
```

No special resume command needed.
