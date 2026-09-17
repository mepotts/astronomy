# ITF alerts through existing GitHub email and phone push

This is the selected route, replacing the unenabled SendGrid/Twilio companion.
No new sender accounts, SMS service, recipient phone number or email address is
stored in code. The existing daily15:00UTC watch posts counts-only notifications
to the configured `ITF daily alerts` issue and mentions `@mepotts`.

## Delivery settings the owner must verify

1. Add/verify the preferred email in [GitHub email settings](https://github.com/settings/emails).
2. In [notification settings](https://github.com/settings/notifications), enable
   Email and On GitHub for participating/@mention notifications; select the
   verified destination email.
3. Install GitHub Mobile, sign into the existing account, enable direct-mention
   push notifications, and allow notifications in phone OS settings. Check quiet
   hours. These are app pushes, **not SMS texts**.
4. Confirm an actual bot alert reaches both inbox and phone. A posted comment is
   not proof of either delivery. No app/account notification settings are changed
   by the workflow or the alert code.

Official [notification guide](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications).

## Triggers and safeguards

- One setup/baseline notice; no claim the existing ready queue is new.
- Newly ready candidates: explicitly **NOT confirmed discoveries**.
- Archive/check failure or stale data: one incident notice and one recovery notice.
- Cache loss: explicit rebuilt-baseline notice, not fabricated candidate movement.
- Quiet otherwise. Disappearance from ITF is not discovery or MPC confirmation.
- No candidate identifiers, coordinates, payloads, recipients or credentials in
  public comments. Human scientific confirmation/submission remains separate.

`ITF_ALERT_ISSUE` is a repository variable containing the dedicated issue number.
The workflow uses its built-in token with contents:read and issues:write; no PAT
or provider key is required. The issue title and repository are validated before
posting. Only `github-actions[bot]` ledger markers are trusted. Comments retain
event hashes and health state; the watch cache advances only after alert delivery
or a successful no-op. An uncertain POST is not retried immediately; a later run
reads the ledger first. Do not delete/edit bot ledger comments or close the issue
without migrating state. At5000 comments the job stops for reviewed rollover.

Only schedule and manual dispatch triggers exist. Workflow concurrency prevents
overlapping publishers. If the workflow cannot start at all, it cannot post its
own failure; keep GitHub Actions failure notifications enabled as a separate
fallback. Scheduled jobs can be delayed;15:00UTC is not a real-time SLA.

The existing Windows archive remains authoritative and unchanged. No local
email/SMS task is installed. `daily-alerts.md` documents the unused alternative.
