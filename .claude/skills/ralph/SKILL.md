---
name: ralph
description: Autonomous AI agent loop framework for iterative feature implementation. Use when you need to implement multi-story features autonomously through repeated AI iterations with fresh context. Ralph orchestrates Amp or Claude Code to complete PRD user stories, running quality gates and tracking progress until all requirements pass. Use for setting up autonomous development workflows, creating or configuring prd.json files, implementing features with multiple sequential user stories, questions about Ralph workflow and file formats, or troubleshooting Ralph iterations and quality gates.
---

# Ralph: Autonomous AI Agent Loop

Ralph is an autonomous loop framework that spawns fresh AI instances (Amp or Claude Code) repeatedly to implement features defined in structured PRD files. Each iteration tackles one user story with clean context, relying on git history, `progress.txt`, and `AGENTS.md` for persistent memory.

## Core Workflow

1. **Define** - Create `prd.json` with user stories sized for single context windows
2. **Launch** - Run `ralph.sh` to start autonomous iteration loop
3. **Iterate** - Ralph spawns fresh AI instances, implements stories, runs quality gates
4. **Track** - Stories marked complete in prd.json, learnings captured in progress.txt
5. **Complete** - Loop exits when all stories pass or max iterations reached

## Quick Start

### Minimal Setup

1. Create `prd.json` in project root:

```json
{
  "branchName": "ralph/my-feature",
  "userStories": [
    {
      "id": 1,
      "title": "Add user profile database schema with name and email fields",
      "passes": false
    },
    {
      "id": 2,
      "title": "Create profile edit form component with validation",
      "passes": false
    },
    {
      "id": 3,
      "title": "Write tests for profile update functionality",
      "passes": false
    }
  ]
}
```

2. Run Ralph:

```bash
# Using Amp (default)
./scripts/ralph/ralph.sh

# Using Claude Code
./scripts/ralph/ralph.sh --tool claude

# With custom iteration limit
./scripts/ralph/ralph.sh --tool claude 20
```

3. Monitor progress:

```bash
# Check completion status
cat prd.json | jq '.userStories[] | {id, title, passes}'

# View learnings
tail progress.txt
```

## Key Design Principles

### Fresh Context Per Iteration

Each iteration spawns a new AI instance with clean context. Memory persists through:
- **Git history** - Previous implementations and commits
- **progress.txt** - Append-only learning log from iterations
- **AGENTS.md** - Discovered patterns and codebase conventions
- **prd.json** - Current completion state

This prevents context window pollution while maintaining continuity.

### Right-Sized Stories

Stories must fit within single context windows. Good sizes:

✓ Add database column with migration
✓ Implement single UI component
✓ Create one server action
✓ Add filter dropdown to existing page

✗ Build entire authentication system
✗ Create complete dashboard
✗ Refactor entire API layer

### Quality Gates Required

Ralph relies on fast feedback loops:
- **Typecheck** - Code correctness validation
- **Tests** - Behavior verification
- **CI** - Integration validation

Without functional quality gates, broken code compounds across iterations.

### Browser Verification for UI

Frontend stories benefit from visual verification:
- Use dev-browser skill if available
- Include browser screenshots in commits
- Verify visual correctness beyond test passage

## File Structure

Ralph operates with these key files:

```
project/
├── prd.json              # Feature definition and tracking
├── progress.txt          # Append-only learning log
├── AGENTS.md            # Codebase patterns and conventions
├── scripts/ralph/       # Ralph installation
│   ├── ralph.sh         # Main loop script
│   └── prompt.md        # Amp prompt template
│   └── CLAUDE.md        # Claude Code prompt template
└── archive/             # Previous runs (auto-created)
```

## Essential Commands

### Launch Ralph
```bash
# Amp with 10 iterations (default)
./scripts/ralph/ralph.sh

# Claude Code with 20 iterations
./scripts/ralph/ralph.sh --tool claude 20
```

### Monitor Progress
```bash
# Completion status
cat prd.json | jq '.userStories[] | {id, title, passes}'

# Recent learnings
tail -20 progress.txt

# Remaining stories count
cat prd.json | jq '[.userStories[] | select(.passes == false)] | length'

# Recent commits
git log --oneline -10
```

### Check Configuration
```bash
# View branch name
cat prd.json | jq -r '.branchName'

# View all stories
cat prd.json | jq '.userStories'
```

## Iteration Loop Details

Each iteration:

1. **Reads prd.json** - Identifies next story where `passes: false`
2. **Reads progress.txt** - Loads previous learnings
3. **Reads AGENTS.md** - Incorporates codebase conventions
4. **Implements story** - AI agent writes code for user story
5. **Runs quality gates** - Executes typecheck and tests
6. **On success:**
   - Commits changes to git
   - Updates `passes: true` in prd.json
   - Appends learnings to progress.txt
   - Updates AGENTS.md with patterns
7. **On failure:**
   - Records issue in progress.txt
   - Attempts fix in next iteration

## Exit Conditions

Ralph terminates when:

1. **All stories pass** - Outputs `<promise>COMPLETE</promise>`
2. **Max iterations reached** - Logs to progress.txt

Resume anytime by running Ralph again - state persists in files.

## Automatic Archiving

When `branchName` changes in prd.json, Ralph archives previous run:

```
archive/2024-03-15-previous-feature/
├── prd.json
└── progress.txt
```

This preserves history when starting new features.

## Common Patterns

### Creating PRD from Requirements

When user provides feature requirements:

1. Break into context-sized stories
2. Sequence dependencies (database → logic → UI → tests)
3. Create prd.json with appropriate branchName
4. Verify story sizes are appropriate

### Resuming Failed Runs

Ralph is stateless - simply run again:

```bash
./scripts/ralph/ralph.sh
```

Ralph reads current state from:
- prd.json (completion status)
- progress.txt (what went wrong)
- git history (previous attempts)

### Customizing for Project

After installation, customize prompt template:

1. Update quality gate commands for your stack
2. Add project-specific conventions
3. Include framework patterns
4. Configure browser verification if applicable

## Troubleshooting

### Story repeatedly fails
- Check progress.txt for error patterns
- Verify quality gates run successfully manually
- Consider splitting story into smaller pieces
- Add missing context to AGENTS.md

### Quality gates timeout
- Optimize test suite for faster feedback
- Increase iteration limit
- Check for hanging processes

### Branch not created
- Ensure git repo is initialized
- Verify prd.json has valid branchName
- Check git permissions

### Tests pass but story marked failed
- Verify quality gate commands in prompt template match project
- Check exit codes of quality gate commands
- Review prompt template configuration

## Detailed Documentation

For comprehensive information, see:

- **[prd-format.md](references/prd-format.md)** - Complete PRD structure, fields, story sizing, examples
- **[setup-guide.md](references/setup-guide.md)** - Installation options, prerequisites, configuration, customization
- **[workflow.md](references/workflow.md)** - Detailed loop explanation, monitoring commands, best practices

## When to Use Ralph

Ralph excels at:
- ✓ Multi-story features requiring sequential implementation
- ✓ Repetitive CRUD operations across multiple models
- ✓ Systematic UI component additions
- ✓ Database schema evolution with migrations
- ✓ Features with clear acceptance criteria

Ralph is not ideal for:
- ✗ Single-story tasks (use AI tool directly)
- ✗ Exploratory refactoring
- ✗ Complex architectural decisions requiring human judgment
- ✗ Features requiring frequent mid-implementation pivots

## Integration with AI Tools

### Amp
- Uses `prompt.md` template
- Configure auto-handoff in `~/.config/amp/settings.json`:
  ```json
  {"amp.experimental.autoHandoff": {"context": 90}}
  ```

### Claude Code
- Uses `CLAUDE.md` template
- Handles context management automatically
- Runs with `--dangerously-skip-permissions` for autonomy

Both tools automatically read AGENTS.md files for context.
