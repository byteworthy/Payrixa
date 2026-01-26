# PRD.json Format Reference

## Structure

The `prd.json` file is the central configuration for Ralph, defining the feature being built and tracking completion status.

```json
{
  "branchName": "ralph/feature-name",
  "userStories": [
    {
      "id": 1,
      "title": "Story description",
      "passes": false
    }
  ]
}
```

## Fields

### branchName (required)
- Git branch for this feature work
- Changing this value triggers archiving of previous run
- Convention: prefix with "ralph/" (e.g., "ralph/add-user-auth")

### userStories (required)
Array of story objects, each containing:

- **id** (number): Unique identifier within the PRD
- **title** (string): Clear, actionable description of the work item
- **passes** (boolean): Completion status
  - `false` = not yet completed
  - `true` = implemented and passing quality gates

## Task Sizing Guidelines

Each story must fit within a single AI context window. Good story sizes:

- Add a database column with migration
- Implement a single UI component
- Add a filter dropdown to an existing page
- Create one server action
- Write tests for a specific function

Oversized stories (split these into multiple stories):

- Build entire authentication system
- Create complete dashboard with multiple views
- Refactor entire API layer

## Story Organization

Stories can be hierarchical with nested structure:

```json
{
  "userStories": [
    {
      "id": 1,
      "title": "Parent feature",
      "passes": false,
      "stories": [
        {
          "id": 1.1,
          "title": "Sub-task 1",
          "passes": false
        },
        {
          "id": 1.2,
          "title": "Sub-task 2",
          "passes": false
        }
      ]
    }
  ]
}
```

## Example PRD

```json
{
  "branchName": "ralph/user-profile",
  "userStories": [
    {
      "id": 1,
      "title": "Add user profile database schema with name, email, bio fields",
      "passes": false
    },
    {
      "id": 2,
      "title": "Create profile edit form component with validation",
      "passes": false
    },
    {
      "id": 3,
      "title": "Implement profile update server action",
      "passes": false
    },
    {
      "id": 4,
      "title": "Add tests for profile update logic",
      "passes": false
    }
  ]
}
```

## Workflow Integration

Ralph reads this file each iteration to:
1. Find stories where `passes: false`
2. Select highest-priority incomplete story
3. Implement the story
4. Update `passes: true` on success
5. Continue until all stories pass or max iterations reached
