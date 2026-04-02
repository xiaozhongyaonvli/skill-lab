# Filtering Rules

Use this file when triaging issues after repository selection.

## Repository Signals

Prefer repositories that have most of these traits:
- clear description and scoped purpose
- recent activity
- open issues with useful labels
- issue tracker actively maintained
- contribution surface that matches the user's interests

Deprioritize repositories that show these traits:
- stale issue tracker
- no labels and no maintainer engagement
- almost all issues already assigned
- issues dominated by feature requests when the user wants debugging work

## Issue Inclusion Rules

Strong positive signals:
- open issue
- no assignee
- beginner-friendly labels such as `good first issue`
- maintainer-friendly labels such as `help wanted`
- bug or debug orientation when the user asks for debugging work
- clear reproduction steps or a bounded scope

Conditional positive signals:
- issue has comments, but they are clarifications rather than ownership claims
- issue has no label match, but the thread and title clearly fit the user's interests

## Issue Exclusion Rules

Exclude or strongly downrank issues when:
- the issue is closed
- the issue is assigned
- the issue references an active PR that appears to address it
- the issue thread includes an explicit ownership claim
- a maintainer already confirmed another contributor is handling it
- the issue scope is so broad that it is unsuitable for the user's preferred difficulty

## Ownership Language Heuristics

Treat these as likely claimed:
- `I can work on this`
- `I would like to take this`
- `assigned to`
- `working on a fix`
- `opened a PR`
- `see PR #123`

Treat these as not yet claimed unless later comments change the status:
- requests for clarification
- questions about reproduction
- maintainer discussion without assigning work
- old "interested" comments with no follow-up and no maintainer acknowledgment

## Confidence Levels

Use one of these output values:

- `high`: no assignee, no linked PR, no ownership comments, thread is quiet or only clarifying
- `medium`: no assignee and no linked PR, but thread has some ambiguous activity
- `low`: possible ownership signs exist, but not enough evidence to exclude completely

## Result Shape

For each issue, keep these fields whenever possible:
- `repository`
- `repository_url`
- `issue_number`
- `title`
- `url`
- `labels`
- `updated_at`
- `assignees`
- `linked_prs`
- `unclaimed_confidence`
- `fit_reason`
- `thread_caveat`
