# Ralph Setup Guide

## Prerequisites

1. **Git repository** - Ralph operates within a git repo
2. **jq** - JSON processing tool (`brew install jq` or `apt install jq`)
3. **AI tool** - Either Amp or Claude Code installed

## Installation Options

### Option 1: Project-Local Installation

Best for project-specific customization and version control.

1. Create ralph directory in your project:
```bash
mkdir -p scripts/ralph
```

2. Download ralph.sh:
```bash
curl -o scripts/ralph/ralph.sh https://raw.githubusercontent.com/snarktank/ralph/main/ralph.sh
chmod +x scripts/ralph/ralph.sh
```

3. Download appropriate prompt template:

For Amp:
```bash
curl -o scripts/ralph/prompt.md https://raw.githubusercontent.com/snarktank/ralph/main/prompt.md
```

For Claude Code:
```bash
curl -o scripts/ralph/CLAUDE.md https://raw.githubusercontent.com/snarktank/ralph/main/CLAUDE.md
```

4. Customize prompts for your project (see Customization section)

### Option 2: Global Skills Installation

Best for using Ralph across multiple projects without duplication.

For Amp:
```bash
mkdir -p ~/.config/amp/skills/ralph
curl -o ~/.config/amp/skills/ralph/ralph.sh https://raw.githubusercontent.com/snarktank/ralph/main/ralph.sh
curl -o ~/.config/amp/skills/ralph/prompt.md https://raw.githubusercontent.com/snarktank/ralph/main/prompt.md
chmod +x ~/.config/amp/skills/ralph/ralph.sh
```

For Claude Code:
```bash
mkdir -p ~/.claude/skills/ralph
curl -o ~/.claude/skills/ralph/ralph.sh https://raw.githubusercontent.com/snarktank/ralph/main/ralph.sh
curl -o ~/.claude/skills/ralph/CLAUDE.md https://raw.githubusercontent.com/snarktank/ralph/main/CLAUDE.md
chmod +x ~/.claude/skills/ralph/ralph.sh
```

## Configuration

### For Amp Users

Configure auto-handoff in `~/.config/amp/settings.json`:

```json
{
  "amp.experimental.autoHandoff": {
    "context": 90
  }
}
```

This enables automatic context handoff when context window reaches 90% capacity.

### For Claude Code Users

No additional configuration required. Claude Code handles context management automatically.

## Customization

After installation, customize the prompt template for your stack:

1. **Quality check commands** - Update typecheck and test commands for your project
2. **Codebase conventions** - Add project-specific patterns and gotchas
3. **Tech stack specifics** - Include framework-specific guidance
4. **Browser verification** - Configure if you have dev-browser skill for UI work

Example customizations:

```markdown
# In your prompt template

## Quality Gates

Run these commands after each story:
- `npm run typecheck` - TypeScript validation
- `npm run test` - Jest test suite
- `npm run lint` - ESLint checks

## Codebase Conventions

- Use Prisma for database access
- Server actions in app/actions/
- Components in app/components/
- Use shadcn/ui components, not raw HTML
```

## Verification

Test your installation:

```bash
# For project-local
./scripts/ralph/ralph.sh --help

# For global installation
~/.claude/skills/ralph/ralph.sh --help
```

## Next Steps

1. Create your first PRD (see prd-format.md)
2. Initialize progress tracking (ralph creates this automatically)
3. Run your first iteration (see workflow.md)
