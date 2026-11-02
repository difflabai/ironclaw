# Mattermost CI notification release

This change migrates repository infrastructure alerts to the self-hosted
`https://chat.255labs.xyz`. Product Slack extensions, adapter credentials,
customer workflows, and hermetic Slack mocks remain product coverage; they are
not infrastructure notification destinations.

## Configuration and cutover

Prepare a private incoming webhook locked to the 255labs `#internal` channel.
Keep the URL in the private migration credential handover, never in Git, workflow
logs, issue text, or screenshots. At the coordinated inventory release blitz,
configure these repository Actions secrets:

| Secret | Producers |
| --- | --- |
| `MAIN_CI_MATTERMOST_WEBHOOK_URLS` | Main-branch CI failure alerts; supports one URL or comma/newline-separated fanout |
| `MATTERMOST_WEBHOOK_URL` | Merge-queue CI failure alerts, Nightly Watchdog, Live Canary report |

There is no fallback to either old Slack secret. Leave the optional canary
webhook empty when notification reporting should remain disabled. The existing
main-alert workflow fails visibly when its required destination is missing;
the watchdog continues to fail for unhealthy/missing nightlies even if delivery
is unconfigured. The canary notifier remains best effort and still performs its
independent GitHub comment/issue work without a chat webhook.

The main alert workflow is renamed to `main-ci-mattermost-alerts.yml` / `Main CI
Mattermost Alerts`. Check its resulting GitHub workflow state after merge;
renaming a workflow can create a new workflow identity. Keep existing disabled
live-canary status and runner labels/routing unchanged. Do not enable credentialed
product canaries as part of a notification release.

Remove the old infrastructure `MAIN_CI_SLACK_WEBHOOK_URLS` and `SLACK_WEBHOOK_URL`
secrets after the acceptance window. Product Slack credentials such as
`IRONCLAW_REBORN_SLACK_BOT_TOKEN`, OAuth values, and test-case matrix entries are
separate and must not be removed by this migration.

## Acceptance and rollback

1. Capture the current source SHA, workflow enable/disable states, and secret
   references privately before the coordinated reviewed merge.
2. Stage the Mattermost secrets, merge through the normal review process, and
   inspect the existing CI run. Run a controlled failure-notification smoke only
   when the release coordinator approves the test post.
3. Check the main/merge-queue payload retains failed steps, annotations, PR/commit
   context, and readable run links. Check the canary report retains status counts,
   warning/infrastructure classifications, grouped QA results, and artifact links.
   Verify user-derived `@channel`/direct mentions are inert.
4. Confirm Mattermost delivery and absence of new Slack alerts before revoking
   the old credentials. Record evidence in the inventory tracker.

Rollback: revert this PR, restore the saved Slack secret references if they were
removed, and restore the previous workflow-state settings. The old notifier path
and main-alert workflow identity return with the revert. No live configuration,
runner registration, application deployment, database, or IAM changes are made
by this preparation PR. Existing product Slack features require no rollback.

## Validation

- 84 live-canary script tests pass, including an HTTP receiver driven through
  notifier `main()`, fallback URL redaction, and unchanged GitHub report behavior.
- Four workflow caller tests execute the real inline shell against captured
  `gh`/`curl` arguments: main fanout, queue PR resolution, missing configuration,
  and watchdog failure semantics. They validate native text payloads and mentions.
- 81 PR-plan tests and the renamed main-alert workflow contract test pass.
- `actionlint` passes for main-alert, watchdog, and Code Style workflows. The
  existing Live Canary matrix references undefined `dispatch_only` and custom
  `ironclaw-live` labels; both diagnostics reproduce on unchanged `origin/main`.
- No Rust, browser, model, or external credentialed canaries are needed for the
  Python/shell notification boundary. No real webhook posts were sent.
