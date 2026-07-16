---
triggers:
- issue to pr
- issue-to-pr
- create pr from
- pr from issue
- pr from github issue
- make a pr
- open a pull request
- turn issue into pr
---

# GitHub Issue → PR Workflow

When the user asks you to create a PR from a GitHub issue, follow this workflow:

## Step 1: Fetch Issue Details

Use the API to fetch the issue details:

```
GET /api/v1/github/issue/{owner}/{repo}/{number}
```

This returns the issue title, body, labels, assignees, and state.

## Step 2: Start the Issue→PR Workflow

Use the API to start the workflow:

```
POST /api/v1/github/issue-to-pr
{
  "repository": "owner/repo",
  "issue_number": <number>,
  "target_branch": "main",
  "draft": false
}
```

This returns:
- `branch_name`: The feature branch to use
- `instructions`: Step-by-step instructions for the agent

## Step 3: Implement the Issue

1. **Create and switch to the feature branch** using git:
   ```bash
   git fetch origin
   git checkout -b <branch_name> origin/<target_branch>
   ```

2. **Implement the changes** described in the issue. Make sure to:
   - Follow the project's coding conventions
   - Write tests for new functionality
   - Update documentation if needed

3. **Commit and push** the changes:
   ```bash
   git add -A
   git commit -m "Fix: <issue title>"
   git push origin <branch_name>
   ```

## Step 4: Create the Pull Request

Use the MCP `create_pr` tool:

```json
{
  "repo_name": "owner/repo",
  "source_branch": "<branch_name>",
  "target_branch": "main",
  "title": "<issue title>",
  "body": "Closes #<issue_number>\n\n<optional description>",
  "draft": false
}
```

Make sure to:
- Include `Closes #<issue_number>` in the PR body to auto-close the issue when merged
- Add relevant labels if the issue had them
- Mention any important context from the issue discussion

## Best Practices

- **Branch naming**: Use `fix/issue-{number}-{title}` for bugs, `feat/issue-{number}-{title}` for features
- **Commit messages**: Reference the issue number in commits: `Fix #123: description`
- **PR description**: Copy relevant context from the issue, don't just say "Fixes #123"
- **Tests**: Always include tests for new functionality
- **Review**: If the PR needs human review, create it as a draft
