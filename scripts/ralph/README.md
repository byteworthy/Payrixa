# Ralph Setup for Django Project

Ralph is now installed and configured for this Django REST Framework project.

## Quick Start

### 1. Create Your PRD

Create `prd.json` in the project root with your user stories:

```bash
cp prd.example.json prd.json
# Edit prd.json with your actual feature requirements
```

Example structure:
```json
{
  "branchName": "ralph/my-feature",
  "userStories": [
    {
      "id": 1,
      "title": "Add User model with name and email fields",
      "passes": false
    },
    {
      "id": 2,
      "title": "Create UserSerializer with validation",
      "passes": false
    }
  ]
}
```

### 2. Launch Ralph

From the project root:

```bash
# Run with Claude Code (10 iterations)
./scripts/ralph/ralph.sh --tool claude

# Run with custom iteration count
./scripts/ralph/ralph.sh --tool claude 20

# Run with Amp (if you have it installed)
./scripts/ralph/ralph.sh --tool amp
```

### 3. Monitor Progress

```bash
# Check completion status
cat prd.json | jq '.userStories[] | {id, title, passes}'

# View learnings from iterations
tail -20 progress.txt

# Count remaining stories
cat prd.json | jq '[.userStories[] | select(.passes == false)] | length'

# See recent commits
git log --oneline -10
```

## How Ralph Works

1. **Reads** `prd.json` to find next incomplete story (`passes: false`)
2. **Reviews** `progress.txt` for previous learnings
3. **Checks** `upstream/AGENTS.md` for codebase patterns
4. **Implements** the story following Django/DRF best practices
5. **Runs Quality Gates**:
   - `pytest` (tests with 25% coverage)
   - `python manage.py check` (Django validation)
   - `python manage.py makemigrations --check` (migration validation)
6. **Commits** changes on success
7. **Updates** `prd.json` marking story as `passes: true`
8. **Logs** learnings to `progress.txt`
9. **Repeats** until all stories pass or max iterations reached

## Story Sizing Guide

Each story should fit in one AI context window:

✅ **Good Sizes**:
- Add database model with 3-5 fields
- Create serializer for existing model
- Implement single ViewSet with basic CRUD
- Add filtering to existing ViewSet
- Write tests for one feature

❌ **Too Large** (split these up):
- Build complete authentication system
- Create entire API with multiple endpoints
- Refactor all serializers
- Implement full user management

## File Structure

```
/workspaces/codespaces-django/
├── prd.json                    # Your feature definition (create this)
├── prd.example.json            # Example template
├── progress.txt                # Auto-generated learning log
├── .last-branch                # Auto-generated branch tracking
├── archive/                    # Auto-generated previous runs
├── scripts/ralph/
│   ├── ralph.sh               # Main Ralph script
│   ├── CLAUDE.md              # Django-customized prompt
│   └── README.md              # This file
└── upstream/
    └── AGENTS.md              # Codebase patterns (updated by Ralph)
```

## Quality Gates

Ralph requires these to pass before committing:

```bash
# Run all tests with coverage
pytest

# Django system check
python manage.py check

# Verify no missing migrations
python manage.py makemigrations --check --dry-run
```

## Tips

1. **Start Small**: Begin with 2-3 simple stories to test the workflow
2. **Review Commits**: Check Ralph's commits after each iteration
3. **Update AGENTS.md**: Ralph learns and documents patterns automatically
4. **Monitor progress.txt**: See what Ralph learned and any issues encountered
5. **Resume Anytime**: Ralph is stateless - just run it again to continue

## Django-Specific Patterns

Ralph knows about:
- Django REST Framework patterns (models → serializers → viewsets → URLs)
- Test organization (`tests_*.py` files)
- Migration workflow
- Filtering with `django_filters`
- JWT authentication
- API documentation with DRF Spectacular

## Troubleshooting

### Ralph keeps failing same story
1. Check `progress.txt` for error patterns
2. Run quality gates manually to see detailed errors
3. Consider splitting the story into smaller pieces
4. Add context to `upstream/AGENTS.md` if needed

### Tests failing
```bash
# Run tests to see detailed output
pytest -v

# Run specific test file
pytest upstream/tests_api.py -v
```

### Migrations issues
```bash
# Check migration status
python manage.py showmigrations

# Create migrations manually if needed
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Example Workflow

```bash
# 1. Create your PRD
cat > prd.json << 'EOF'
{
  "branchName": "ralph/add-claims-filter",
  "userStories": [
    {
      "id": 1,
      "title": "Add FilterSet for ClaimRecord with date_range and status filters",
      "passes": false
    },
    {
      "id": 2,
      "title": "Update ClaimRecordViewSet to use the new FilterSet",
      "passes": false
    },
    {
      "id": 3,
      "title": "Write tests for filtering functionality",
      "passes": false
    }
  ]
}
EOF

# 2. Launch Ralph
./scripts/ralph/ralph.sh --tool claude 15

# 3. Monitor (in another terminal)
watch -n 5 'cat prd.json | jq ".userStories[] | {id, passes}"'

# 4. Review results
git log --oneline -10
cat progress.txt
```

## Next Steps

1. Copy `prd.example.json` to `prd.json`
2. Edit `prd.json` with your feature requirements
3. Run `./scripts/ralph/ralph.sh --tool claude`
4. Monitor progress and review commits

For more information, see the Ralph skill documentation or visit https://github.com/snarktank/ralph
